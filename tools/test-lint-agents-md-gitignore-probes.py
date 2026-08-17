#!/usr/bin/env python3
"""`tools/lint-agents-md.py` check 10e — the session-scratch gitignore probes.

T6 of `docs/specs/lint-performance-p0`. Three properties, and the third is the
one that matters:

1. The three probes resolve in **exactly one** `git check-ignore` process, down
   from one per probe.

2. A probe that is not ignored still produces its existing `drift-watch:` note,
   with the existing wording and the existing fatal semantics. `note()` in that
   lint sets ``fail = 1``, so this check *fails the lint* — its assertion is
   inverted relative to the boundary lint, which skips ignored paths.

3. When Git cannot answer at all, the lint says **so**. This is the one
   deliberate behaviour change in the task, and it is asserted rather than
   assumed. Before: an unhandled ``FileNotFoundError`` traceback. A naive
   fail-open would be worse than the traceback — it would emit three notes
   claiming `.gitignore` drifted, which is a *false diagnosis* of a real
   degradation: the operator is told to go fix a gitignore file that is fine.
   So a degraded resolution names Git unavailability and exits non-zero.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parents[1]
LINTER = REPO_ROOT / "tools" / "lint-agents-md.py"

#: A single ~400-line main() aborts every later block on one exception, so the
#: reported count silently drops. Falling below this is a failure in itself.
_CASE_FLOOR = 28

_FAILURES: list[str] = []
_CASES = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global _CASES
    _CASES += 1
    if not ok:
        _FAILURES.append(f"{name}: {detail}" if detail else name)


def _run(extra_env: dict[str, str] | None = None,
         path_prefix: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if path_prefix is not None:
        env["PATH"] = f"{path_prefix}{os.pathsep}{env.get('PATH', '')}"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(LINTER)], cwd=str(REPO_ROOT),
        capture_output=True, text=True, check=False, env=env,
    )


def _counting_git_shim(directory: Path, log: Path, real_git: str) -> None:
    """A `git` earlier on PATH that records its argv and delegates."""
    directory.mkdir(parents=True, exist_ok=True)
    shim = directory / "git"
    shim.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{log}"\n'
        f'exec {real_git} "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)


def _absent_git_shim(directory: Path) -> None:
    """A `git` that is not executable as git — simulates Git being unusable."""
    directory.mkdir(parents=True, exist_ok=True)
    shim = directory / "git"
    shim.write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
    shim.chmod(0o755)


def main() -> int:
    import shutil
    import tempfile

    real_git = shutil.which("git")
    if real_git is None:
        sys.stderr.write("SKIP no git on PATH — this suite needs a real git\n")
        return 0

    with tempfile.TemporaryDirectory(prefix="agents-md-probes-") as td:
        tmp = Path(td)

        # ---- one batched process, not one per probe --------------------
        log = tmp / "git-calls.log"
        log.write_text("", encoding="utf-8")
        shim_dir = tmp / "shim"
        _counting_git_shim(shim_dir, log, real_git)
        proc = _run(path_prefix=shim_dir)
        calls = [c for c in log.read_text(encoding="utf-8").splitlines() if c.strip()]
        check_ignore_calls = [c for c in calls if c.startswith("check-ignore")]
        check("lint still passes on the real tree", proc.returncode == 0,
              f"rc={proc.returncode}\n{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}")
        check("exactly one check-ignore process",
              len(check_ignore_calls) == 1,
              f"{len(check_ignore_calls)} calls: {check_ignore_calls}")
        check("candidates go over stdin, not argv",
              all("state.json" not in c for c in check_ignore_calls),
              f"{check_ignore_calls}")

        # ---- the probes are genuinely ignored in this repo -------------
        # If they were not, the note path below would fire on a clean tree and
        # this suite would be asserting nothing about the happy path.
        check("no drift-watch note on a clean tree",
              "drift-watch" not in proc.stderr, proc.stderr[-800:])

        # ---- the not-ignored note keeps its exact pre-change wording ----
        # Run the LINT, not a reconstruction. An earlier version compared two
        # string literals defined in this file, which cannot fail no matter what
        # the lint prints — and the batching change reindented that f-string,
        # which is exactly how a message drifts unnoticed.
        sandbox = tmp / "wording"
        (sandbox / "docs" / "specs" / "example").mkdir(parents=True)
        (sandbox / "docs" / "specs" / "example" / "state.json").write_text(
            "{}", encoding="utf-8"
        )
        (sandbox / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
        try:
            (sandbox / "CLAUDE.md").symlink_to("AGENTS.md")
        except OSError:
            # Windows without Developer Mode: the lint accepts a materialised
            # symlink (a regular file whose content is the link target), which is
            # exactly the shape check #2 documents.
            (sandbox / "CLAUDE.md").write_text("AGENTS.md", encoding="utf-8")
        (sandbox / "docs").mkdir(exist_ok=True)
        (sandbox / "docs" / "CHARTER.md").write_text("# charter\n", encoding="utf-8")
        for quadrant in ("tutorials", "how-to", "reference", "explanation"):
            (sandbox / "guides" / quadrant).mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "."], cwd=str(sandbox),
                       capture_output=True, check=True)
        (sandbox / ".gitignore").write_text("", encoding="utf-8")

        expected = (
            "drift-watch: 'docs/specs/example/state.json' should be gitignored "
            "(session-scratch — see "
            ".claude/skills/work-loop/references/state-schema.md, "
            "CONVENTIONS.md#supervisor-mode)."
        )
        wording = subprocess.run(
            [sys.executable, str(LINTER)], cwd=str(sandbox),
            capture_output=True, text=True, check=False,
            env={**os.environ, "GIT_CEILING_DIRECTORIES": str(tmp)},
        )
        emitted = wording.stdout + wording.stderr
        check("an un-ignored probe produces the drift note",
              "should be gitignored" in emitted, emitted[-600:])
        check("the note wording is byte-identical to the pre-change text",
              expected in emitted,
              f"expected substring absent.\n  want: {expected!r}\n"
              f"  got: {[ln for ln in emitted.splitlines() if 'drift-watch' in ln]}")
        check("an un-ignored probe fails the lint (note() is fatal)",
              wording.returncode != 0, f"rc={wording.returncode}")

        # ---- Git unusable: name the cause, do not blame .gitignore -----
        # Two distinct shapes, because they take different code paths today:
        # a git that RUNS and fails (exit 127) currently emits three false
        # drift notes, and a git that is ABSENT currently tracebacks.
        for label, prep in (
            ("broken git (exit 127)", _absent_git_shim),
            ("absent git (empty PATH dir)", lambda d: d.mkdir(parents=True,
                                                              exist_ok=True)),
        ):
            probe_dir = tmp / label.split()[0]
            prep(probe_dir)
            # An empty PATH dir means git is ABSENT (FileNotFoundError); a dir
            # holding a failing `git` means git is BROKEN (non-zero exit). The
            # two took different code paths before this change, so they are
            # driven differently on purpose.
            absent_shape = prep is not _absent_git_shim
            run = (_run(extra_env={"PATH": str(probe_dir)}) if absent_shape
                   else _run(path_prefix=probe_dir))
            merged = run.stdout + run.stderr
            check(f"{label}: exits non-zero", run.returncode != 0,
                  f"rc={run.returncode}")
            check(f"{label}: no traceback",
                  "Traceback (most recent call last)" not in merged,
                  merged[-600:])
            check(f"{label}: does NOT claim .gitignore drifted",
                  "should be gitignored" not in merged,
                  "false drift note while git was unusable")

        absent = tmp / "absent"
        _absent_git_shim(absent)
        degraded = _run(path_prefix=absent)
        combined = degraded.stdout + degraded.stderr
        check("degraded run exits non-zero", degraded.returncode != 0,
              f"rc={degraded.returncode}")
        check("degraded run does not traceback",
              "Traceback (most recent call last)" not in combined,
              combined[-800:])
        check("degraded run names git unavailability",
              any(t in combined.lower() for t in
                  ("git is unavailable", "git unavailable", "could not be executed",
                   "git check-ignore could not", "gitignore probes could not")),
              combined[-1200:])
        check("degraded run does NOT claim .gitignore drifted",
              "should be gitignored" not in combined,
              "emitted the drift note while git was unusable: "
              + combined[-800:])

    # ---- the two refusal branches, which no PATH shim can reach ---------
    # A hostile PATH produces git-ABSENT or git-BROKEN. It cannot produce the two
    # REFUSAL states: git exiting 128 on an unusable candidate, and the resolver
    # declining before launch. Those are driven in-process, because the remedy
    # differs — "re-run where git works" is actively wrong for both, and that
    # exact conflation was a review finding against this lint's sibling.
    import importlib.util

    spec = importlib.util.spec_from_file_location("lint_agents_md", LINTER)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(REPO_ROOT / "tools"))

    real_resolver = module.lint_git_ignore.git_ignored_paths
    # `main()` opens with `os.chdir(_repo_root())`, and `_repo_root()` runs
    # `git rev-parse --show-toplevel` from the CURRENT directory. Launched from
    # outside the repo that resolves to the wrong root and the lint then walks a
    # foreign tree — verified: from `/tmp` it reaches a stale pytest fixture and
    # dies on a dangling `AGENTS.md`. That is pre-existing linter behaviour (it is
    # invoked from a pre-PR hook, always inside the repo) and is not this spec's to
    # change; but the subprocess cases pin `cwd=REPO_ROOT`, so an in-process call
    # must do the same or this suite becomes the one thing in the tree that fails
    # by launch directory. Enter the repo root first, and restore afterwards
    # because `main()` never does.
    original_cwd = Path.cwd()
    # Launch-directory independence is asserted, not merely arranged. Deleting the
    # `os.chdir(REPO_ROOT)` inside the loop leaves this suite green from the repo
    # root — the only way CI and `test-all.py` invoke it — while failing anywhere
    # else, so without a case pinning it the defect returns invisibly.
    #
    # The foreign launch directory must itself be a Git repository. `_repo_root()`
    # shells out to `git rev-parse --show-toplevel`; from a plain temp directory
    # that fails and the fallback returns a safe root, so a bare `mkdtemp` does not
    # reproduce the defect — verified, the mutation stayed green against one. A
    # `git init`-ed directory makes `rev-parse` succeed and hand back the WRONG
    # root, which is the real failure mode.
    # `.resolve()`: on macOS `mkdtemp` hands back `/var/folders/…` while
    # `Path.cwd()` reports the real `/private/var/folders/…`, so the restore
    # assertion would compare two spellings of the same directory and fail.
    foreign = Path(tempfile.mkdtemp(prefix="probe-foreign-repo-")).resolve()
    subprocess.run(["git", "init", "-q", "."], cwd=str(foreign),
                   capture_output=True, check=True,
                   env=module.lint_git_ignore.hermetic_git_env(
                       os.environ, repo_root=foreign))
    (foreign / "AGENTS.md").write_text("# decoy\n", encoding="utf-8")
    # The decoy alone is not enough either: `main()` re-chdirs to whatever
    # `_repo_root()` returns, still reaches check 10e, and emits the same refusal
    # wording — verified, the mutation stayed green against it. What actually broke
    # the suite from `/tmp` was `Path().rglob("AGENTS.md")` reaching a **dangling**
    # `AGENTS.md` left by an unrelated pytest run and dying in `read_text`. So plant
    # exactly that. With the fix the foreign tree is never walked; without it, this
    # raises `FileNotFoundError` and the suite cannot report green.
    (foreign / "sub").mkdir()
    (foreign / "sub" / "AGENTS.md").symlink_to(foreign / "gone-missing.md")
    for launch_dir in (REPO_ROOT, foreign):
        os.chdir(launch_dir)
        _refusal_branch_cases(module, real_resolver)
        # Asserted per launch directory, and that is the point: comparing against
        # the SUITE's own cwd would be vacuous, because CI launches from the repo
        # root and the helper enters the repo root anyway — the check would pass
        # whether or not it restored anything. Comparing against the directory the
        # helper was *called in* has teeth in both iterations.
        check(f"the in-process block restores the cwd it was called in "
              f"({'repo root' if launch_dir == REPO_ROOT else 'foreign repo'})",
              Path.cwd() == launch_dir, f"{Path.cwd()} != {launch_dir}")
    os.chdir(original_cwd)

    if _CASES < _CASE_FLOOR:
        _FAILURES.append(
            f"only {_CASES} cases ran, below the floor of {_CASE_FLOOR}; a run "
            f"that stops early must not report green"
        )
    for f in _FAILURES:
        sys.stderr.write(f"FAIL {f}\n")
    if _FAILURES:
        sys.stderr.write(
            f"\u2716 lint-agents-md gitignore probes: {len(_FAILURES)} of {_CASES} "
            f"failed\n"
        )
        return 1
    sys.stderr.write(f"ok — {_CASES} cases passed\n")
    return 0


def _refusal_branch_cases(module, real_resolver) -> None:
    """The two refusal branches, driven in-process.

    `main()` opens with `os.chdir(_repo_root())`, and `_repo_root()` runs
    `git rev-parse --show-toplevel` from the CURRENT directory — so this must enter
    the repository itself, exactly as the subprocess cases do with `cwd=REPO_ROOT`.
    The `finally` restores the cwd this helper was CALLED in — not the repo root —
    even if `main()` raises something other than `SystemExit`, which would otherwise
    strand the process wherever `main()` left it.
    """
    entry_cwd = Path.cwd()
    for label, exc, want, must_not in (
        ("git refused the batch",
         module.lint_git_ignore.GitIgnoreError("exit 128: outside repository"),
         "git rejected the probe batch", "re-run where git works"),
        ("resolver refused pre-launch",
         ValueError("candidate escapes the repository root"),
         "refused before git was called", "re-run where git works"),
    ):
        def _raising(*_a, _exc=exc, **_kw):
            raise _exc

        module.lint_git_ignore.git_ignored_paths = _raising
        buffer = io.StringIO()
        os.chdir(REPO_ROOT)
        try:
            with contextlib.redirect_stdout(buffer), \
                    contextlib.redirect_stderr(buffer):
                module.main()
        except SystemExit:
            pass
        finally:
            module.lint_git_ignore.git_ignored_paths = real_resolver
            os.chdir(entry_cwd)   # main() chdirs and never restores
        emitted = buffer.getvalue()
        check(f"{label}: names its own cause",
              want in emitted, emitted[-700:])
        check(f"{label}: does not send the reader to another machine",
              must_not not in emitted, emitted[-700:])
        check(f"{label}: does NOT claim .gitignore drifted",
              "should be gitignored" not in emitted, emitted[-700:])


if __name__ == "__main__":
    raise SystemExit(main())
