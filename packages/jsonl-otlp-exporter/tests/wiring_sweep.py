"""Mutation sweep over the defect class this package keeps producing.

Six times across four review rounds a rule was applied at one call site and not
at its sibling -- a keyword passed here and not there. Every one passed the full
suite. This removes each cross-module keyword in turn and reports the ones
nothing notices; a survivor is a wiring with no control behind it.

Run it from anywhere:

    python3 packages/jsonl-otlp-exporter/tests/wiring_sweep.py

Four lessons are built in, each from a way an earlier version misled someone.

1. Paths are derived from `__file__`, never from the working directory. Run from
   the repository root, an earlier version resolved `pytest tests` against the
   REPO's `tests/` -- conformance, fixtures and roster -- which timed out on
   every mutation and reported fifteen `HUNG` lines. Fifteen hangs look like
   fifteen defects in the code under test, and nothing in the output said "I ran
   a different suite". That is the same failure this sweep exists to find: a gate
   that reports findings rather than an error.

2. The target suite is verified before any mutation, so a wrong path fails loudly
   and immediately rather than as a wall of false positives.

3. Mutations survive a crash. The original is written to a sidecar first, and a
   leftover sidecar is restored on the next start. An earlier version mutated in
   place inside a `try/finally`, which does not survive SIGKILL -- killing it left
   `cli.py` missing a `timeout=` argument, indistinguishable in `git status` from
   a real edit.

4. Results are written as they are produced. The first version printed only after
   its loop and was killed by a hanging mutation after thirty minutes, producing
   nothing at all.
"""
import ast
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
PACKAGE_ROOT = HERE.parents[1]
PKG = PACKAGE_ROOT / "jsonl_otlp_exporter"
TESTS = PACKAGE_ROOT / "tests"
OUT = PACKAGE_ROOT / "wiring-sweep-results.txt"
SIDECAR_SUFFIX = ".wiring-sweep-backup"
PER_RUN_SECONDS = 90

# Keywords whose removal is not a behaviour change worth reporting. Argparse
# display text is here because it produced survivors on every earlier run that a
# human then had to triage by hand -- `help=`, `prog=` and `description=` cannot
# fail a test, so reporting them buries the behavioural survivors among noise.
SKIP = {
    "file", "encoding", "errors", "default", "dir_fd", "key", "reverse",
    "help", "prog", "description", "metavar", "dest",
}


def restore_any_leftover_mutation() -> None:
    """Undo a mutation a previous run was killed in the middle of."""
    for sidecar in PKG.glob(f"*{SIDECAR_SUFFIX}"):
        target = sidecar.with_suffix("")
        target.write_text(sidecar.read_text(), encoding="utf-8")
        sidecar.unlink()
        print(f"restored {target.name} from a killed earlier run", flush=True)


def verify_target_suite() -> None:
    """Prove we are about to run THIS package's suite, not some other one."""
    if not TESTS.is_dir() or not (TESTS / "unit").is_dir():
        sys.exit(f"no test suite at {TESTS} -- refusing to run a different one")
    # NOT `-q`: with it, pytest prints per-file counts and no total, so the
    # size line read "unknown size" -- a diagnostic that silently says nothing is
    # the same class of defect this whole script exists to catch.
    probe = subprocess.run(
        [sys.executable, "-m", "pytest", str(TESTS), "--co"],
        capture_output=True, text=True, cwd=PACKAGE_ROOT, timeout=PER_RUN_SECONDS)
    if probe.returncode != 0:
        sys.exit(f"the suite at {TESTS} does not collect cleanly:\n{probe.stdout[-2000:]}")
    collected = [ln for ln in probe.stdout.splitlines() if "tests collected" in ln]
    print(f"target suite: {TESTS}  ({collected[-1] if collected else 'unknown size'})",
          flush=True)


def wirings():
    for path in sorted(PKG.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg is None or kw.arg in SKIP:
                    continue
                seg = ast.get_source_segment(source, kw)
                if seg:
                    yield path, kw.lineno, seg


def run_suite() -> str:
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", str(TESTS), "-q", "-x"],
            capture_output=True, text=True, cwd=PACKAGE_ROOT,
            timeout=PER_RUN_SECONDS)
        return "SURVIVED" if r.returncode == 0 else "caught"
    except subprocess.TimeoutExpired:
        return "HUNG"


def main() -> int:
    restore_any_leftover_mutation()
    verify_target_suite()

    seen: set[tuple[str, str]] = set()
    survivors = 0
    with OUT.open("w", encoding="utf-8") as log:
        for path, lineno, seg in wirings():
            key = (path.name, seg)
            if key in seen:
                continue
            seen.add(key)
            original = path.read_text(encoding="utf-8")
            for candidate in (seg + ", ", seg + ",\n", ", " + seg, seg):
                if candidate in original:
                    mutated = original.replace(candidate, "", 1)
                    break
            else:
                continue
            try:
                compile(mutated, str(path), "exec")
            except SyntaxError:
                continue

            sidecar = path.with_suffix(path.suffix + SIDECAR_SUFFIX)
            sidecar.write_text(original, encoding="utf-8")
            path.write_text(mutated, encoding="utf-8")
            try:
                verdict = run_suite()
            finally:
                path.write_text(original, encoding="utf-8")
                sidecar.unlink(missing_ok=True)

            line = f"{verdict:9} {path.name}:{lineno}  {seg}"
            log.write(line + "\n")
            log.flush()
            print(line, flush=True)
            if verdict == "SURVIVED":
                survivors += 1

    print(f"\n{len(seen)} wirings mutated, {survivors} survived", flush=True)
    return 1 if survivors else 0


if __name__ == "__main__":
    raise SystemExit(main())
