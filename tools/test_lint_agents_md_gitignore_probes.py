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

import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parents[1]
LINTER = REPO_ROOT / "tools" / "lint-agents-md.py"

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
        # The batching change reindented this f-string, which is exactly how a
        # message silently drifts. Pin the bytes against a fixture where the
        # probe genuinely is not ignored.
        sandbox = tmp / "wording"
        (sandbox / "docs" / "specs" / "example").mkdir(parents=True)
        (sandbox / "docs" / "specs" / "example" / "state.json").write_text(
            "{}", encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q", "."], cwd=str(sandbox),
                       capture_output=True, check=True)
        (sandbox / ".gitignore").write_text("", encoding="utf-8")
        expected = (
            "drift-watch: 'docs/specs/example/state.json' should be gitignored "
            "(session-scratch — see "
            ".claude/skills/work-loop/references/state-schema.md, "
            "CONVENTIONS.md#supervisor-mode)."
        )
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("_agents_md_probe_mod", LINTER)
        _mod = _ilu.module_from_spec(_spec)
        sys.modules["_agents_md_probe_mod"] = _mod
        _sys_path0 = sys.path[0]
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        try:
            _spec.loader.exec_module(_mod)
            resolution = _mod.lint_git_ignore.git_ignored_paths(
                sandbox, [Path("docs/specs/example/state.json")],
                missing_git_policy=_mod.lint_git_ignore.MissingGitPolicy.FAIL_OPEN,
                timeout=30.0,
            )
            not_ignored = Path("docs/specs/example/state.json") not in set(
                resolution.ignored
            )
        finally:
            sys.path.remove(str(REPO_ROOT / "tools"))
        check("an un-ignored probe is detected as such in a bare sandbox",
              not_ignored, repr(resolution))
        # The wording itself, reassembled the way the lint assembles it.
        probe = "docs/specs/example/state.json"
        assembled = (
            f"drift-watch: '{probe}' should be gitignored "
            f"(session-scratch — see "
            f".claude/skills/work-loop/references/state-schema.md, "
            f"CONVENTIONS.md#supervisor-mode)."
        )
        check("note wording is byte-identical to the pre-change text",
              assembled == expected, f"{assembled!r} != {expected!r}")

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
            env = {"PATH": str(probe_dir)} if "absent" in label else None
            run = (_run(extra_env=env) if env
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

    for f in _FAILURES:
        sys.stderr.write(f"FAIL {f}\n")
    if _FAILURES:
        sys.stderr.write(
            f"✖ lint-agents-md gitignore probes: {len(_FAILURES)} of {_CASES} "
            f"failed\n"
        )
        return 1
    sys.stderr.write(f"ok — {_CASES} cases passed\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
