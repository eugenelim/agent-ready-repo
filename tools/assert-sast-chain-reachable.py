#!/usr/bin/env python3
"""Assert `make build-check` can still reach its `$(MAKE) sast` branch.

# STUB: AC10 (spec/ci-gate-parallelization)

## Why this exists

ADR-0086 moves the SAST/SCA leg into its own `gate-sast` CI job, and `gate-main`
invokes `make build-check` with `SAST_DELEGATED=1` on the command line. After that
change **no CI path executes the `$(MAKE) sast` branch inside `build-check`** — so
deleting that branch would go green everywhere, and ADR-0086's central claim (the
Makefile chain survives, which is what ADR-0017's dogfooding rationale actually
required) would be true only by assertion.

This pins it. It asserts **reachability**, not text presence: grepping the Makefile
for `$(MAKE) sast` passes even when the branch has been made unreachable, e.g. by
defaulting `SKIP_SAST` non-empty.

## Three mechanism traps, each of which broke an earlier draft of this check

1. **`build_gate_chain.py` is the make-free Windows contributor entry point** — a
   shipped acceptance criterion of `spec/local-gate-ci-parity`. A hard `make`
   dependency would fail there, so this skips cleanly when `make` is absent.
2. **GNU Make exports command-line overrides to child makes** via `MAKEFLAGS` /
   `MAKEOVERRIDES`. Invoked from inside `gate-main`'s
   `make build-check … SAST_DELEGATED=1`, a nested `make -n build-check` would
   inherit that assignment, take the delegated branch, and red-fail on every CI run
   — after which the tempting fix is to weaken this check. The child environment is
   therefore scrubbed.
3. **Make *executes* rather than prints recipe lines containing `$(MAKE)` under
   `-n`.** So grepping the `-n` output for the literal `$(MAKE) sast` finds nothing;
   what appears instead is the *sub-make's expanded recipe*. This keys on a marker
   unique to that expansion.

Exit codes: 0 = reachable (or `make` absent), 1 = unreachable.
"""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# A token that appears only in the `sast` recipe's expansion. `$(MAKE) sast` itself
# never appears in `-n` output (trap 3), and this must not be a string that also
# occurs in a comment — the -n output includes recipe comments.
MARKER = "run-bandit-gate.py"

# Trap 2: everything that could make the child take a different branch.
_SCRUB = ("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS",
          "SAST_DELEGATED", "SKIP_SAST")


def _child_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _SCRUB}
    if extra:
        env.update(extra)
    return env


def _reaches_sast(makefile: pathlib.Path | None = None,
                  extra_env: dict[str, str] | None = None) -> tuple[bool, str]:
    """Does a dry run of `build-check` reach the sast recipe?"""
    argv = ["make", "-n"]
    if makefile is not None:
        argv += ["-f", str(makefile)]
    argv.append("build-check")
    res = subprocess.run(argv, cwd=REPO_ROOT, env=_child_env(extra_env),
                         capture_output=True, text=True, check=False)
    out = res.stdout + res.stderr
    return (MARKER in out, out)


def self_test() -> int:
    """Mutation-prove the check, including under the parent environment it runs in."""
    failures: list[str] = []
    src = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    ok, _ = _reaches_sast()
    if not ok:
        failures.append("baseline: real Makefile should reach the sast recipe")

    # The trap-2 case: the parent invocation's own assignment must not leak in.
    ok, _ = _reaches_sast(extra_env={"SAST_DELEGATED": "1"})
    if not ok:
        failures.append(
            "scrub failed: an inherited SAST_DELEGATED took the delegated branch")

    with tempfile.TemporaryDirectory() as td:
        # Mutation 1: the branch is deleted outright.
        deleted = re.sub(r"\t\t\$\(MAKE\) sast; \\\n", "\t\ttrue; \\\n", src)
        if deleted == src:
            failures.append("mutation 1: no-op transform — proves nothing")
        mk = pathlib.Path(td) / "deleted.mk"
        mk.write_text(deleted, encoding="utf-8")
        ok, _ = _reaches_sast(mk)
        if ok:
            failures.append("mutation 1: deleting `$(MAKE) sast` was not detected")

        # Mutation 2: the branch survives textually but is made UNREACHABLE — the
        # case a grep for `$(MAKE) sast` cannot distinguish from a healthy chain.
        neutered = src.replace(
            "build-check:\n", "build-check: SKIP_SAST := 1\nbuild-check:\n", 1)
        if neutered == src:
            failures.append("mutation 2: no-op transform — proves nothing")
        mk2 = pathlib.Path(td) / "neutered.mk"
        mk2.write_text(neutered, encoding="utf-8")
        ok, _ = _reaches_sast(mk2)
        if ok:
            failures.append(
                "mutation 2: an unreachable-but-present branch was not detected")

    if failures:
        print(f"✖ assert-sast-chain-reachable self-test: {len(failures)} problem(s):",
              file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("✓ assert-sast-chain-reachable: self-test passed "
          "(baseline reachable; deletion and neutering both detected; scrub holds)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        if not shutil.which("make"):
            print("… assert-sast-chain-reachable self-test skipped: no `make` on PATH")
            return 0
        return self_test()

    # Same reasoning as the posture test: prove the check before trusting it.
    if shutil.which("make") and self_test() != 0:
        return 1
    # Trap 1: the make-free Windows contributor path.
    if not shutil.which("make"):
        print("… assert-sast-chain-reachable skipped: no `make` on PATH "
              "(make-free contributor path — spec/local-gate-ci-parity)")
        return 0

    ok, out = _reaches_sast()
    if ok:
        print("✓ make build-check still reaches the SAST/SCA leg "
              "(ADR-0086 keeps the Makefile chain intact for local dogfooding)")
        return 0
    print("✖ make build-check no longer reaches its `$(MAKE) sast` branch.\n"
          f"   Expected {MARKER!r} in the output of `make -n build-check`.\n"
          "   No CI path executes that branch since ADR-0086, so this check is the\n"
          "   only thing standing between the local gate and a silent regression.\n"
          "   If the branch was intentionally removed, ADR-0086's rationale no longer\n"
          "   holds and needs revisiting — do not delete this check to go green.",
          file=sys.stderr)
    sys.stderr.write(out[-1500:] if out else "(no output)\n")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
