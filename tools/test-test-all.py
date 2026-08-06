#!/usr/bin/env python3
"""Self-test for tools/test-all.py's manifest preflight.

The umbrella runner sat red for weeks because two `TESTS` entries named files
that were never on `main`, and the runner reported that as "2 of 9 failed" — a
sentence about tests that ran. This suite pins the distinction the runner now
draws: a broken manifest exits 2 and runs nothing; a real test failure exits 1.

Pure-stdlib Python so the suite runs on Windows without an MSYS shell.

Case 5 is the standing regression guard: it asserts the *live* `TESTS` list
resolves against the real tree, so a future entry that names a missing file
fails here in a second rather than at the bottom of a multi-minute suite run.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "tools" / "test-all.py"

_FAILURES: list[str] = []
_CASES = 0


def _utf8_streams() -> None:
    """Windows cp1252 guard — UTF-8 streams before any glyph is printed.

    Called from `main`, not at import, so importing this module for its pure
    functions does not reconfigure the importer's streams.
    """
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def _load_runner():
    """Import tools/test-all.py by path — the filename is not a legal module name."""
    spec = importlib.util.spec_from_file_location("_test_all_under_test", RUNNER)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        raise RuntimeError(f"cannot load {RUNNER}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _check(name: str, got: object, want: object) -> None:
    global _CASES
    _CASES += 1
    if got != want:
        _FAILURES.append(f"{name}: got {got!r}, want {want!r}")


def _check_in(name: str, needle: str, haystack: str) -> None:
    global _CASES
    _CASES += 1
    if needle not in haystack:
        _FAILURES.append(f"{name}: missing {needle!r} in output\n  output: {haystack!r}")


def main() -> int:
    _utf8_streams()
    M = _load_runner()

    # 1. Target extraction: the script/pytest paths, not the interpreter or flags.
    _check(
        "entry-targets-pytest",
        M._entry_targets([sys.executable, "-m", "pytest", "a/b/test_x.py", "-v"]),
        ["a/b/test_x.py"],
    )
    _check(
        "entry-targets-bash",
        M._entry_targets(["bash", "tools/test-pre-pr.sh"]),
        ["tools/test-pre-pr.sh"],
    )
    _check(
        "entry-targets-drops-interpreter",
        M._entry_targets([sys.executable, "x.py"]),
        ["x.py"],
    )

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        (tmp / "sub").mkdir()
        (tmp / "sub" / "present.py").write_text("", encoding="utf-8")

        # 2. Intact manifest → no findings.
        _check(
            "missing-none",
            M._missing_targets([("ok", [sys.executable, "sub/present.py"])], tmp),
            [],
        )

        # 3. Absent target → reported with its label so the entry is nameable.
        _check(
            "missing-one",
            M._missing_targets([("gone", [sys.executable, "sub/absent.py"])], tmp),
            [("gone", "absent", "sub/absent.py")],
        )

        # 3b. An entry naming nothing verifiable is a manifest error too — a
        #     bare `-m pytest` would otherwise preflight clean while checking
        #     nothing at all. The kind is returned, not sniffed from the message.
        opaque = M._missing_targets([("opaque", [sys.executable, "-m", "pytest"])], tmp)
        _check("no-verifiable-target-count", len(opaque), 1)
        _check("no-verifiable-target-label", opaque[0][0], "opaque")
        _check("no-verifiable-target-kind", opaque[0][1], "unverifiable")
        _check_in("no-verifiable-target-reason", "no verifiable target", opaque[0][2])

        # 4. Real invocation in a tree where nothing resolves: exit 2, nothing
        #    run. The child's git env is scrubbed and ceilinged: `_repo_root()`
        #    shells out to `git rev-parse --show-toplevel`, which honours an
        #    inherited GIT_DIR / GIT_WORK_TREE — under `git bisect run` or
        #    `git rebase --exec`, or with TMPDIR inside a checkout, an
        #    unscrubbed child would resolve to the real repo, find every entry,
        #    and run the whole multi-minute suite before failing with a
        #    misleading exit-0.
        empty = tmp / "empty-repo"
        empty.mkdir()
        init = subprocess.run(["git", "init", "-q", str(empty)], check=False,
                              capture_output=True, text=True)
        _check("git-init-succeeded", init.returncode, 0)
        env = {k: v for k, v in os.environ.items()
               if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
        env["GIT_CEILING_DIRECTORIES"] = str(tmp)
        res = subprocess.run(
            [sys.executable, str(RUNNER)],
            cwd=str(empty), env=env, capture_output=True, text=True, check=False,
        )
        out = res.stdout + res.stderr
        _check("broken-manifest-exit", res.returncode, 2)
        _check_in("broken-manifest-banner", "BROKEN MANIFEST", out)
        _check_in("broken-manifest-no-run", "no tests were run", out)
        # Everything missing is a wrong-root diagnosis, not restore-or-remove
        # advice — the latter would be advice to delete a correct manifest.
        _check_in("broken-manifest-wrong-root", "wrong repository root", out)
        # A ✓/✖ per-test line would mean the preflight failed to short-circuit.
        _check("broken-manifest-ran-nothing", "✓ " in out, False)

    # 5. The live manifest resolves against the real tree.
    _check("live-manifest-intact", M._missing_targets(M.TESTS, REPO_ROOT), [])

    if _FAILURES:
        print(f"✖ {len(_FAILURES)}/{_CASES} cases failed:")
        for f in _FAILURES:
            print(f"  - {f}")
        return 1
    print(f"✓ all {_CASES} cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
