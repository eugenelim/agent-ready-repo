"""Mutation sweep over the defect class this package keeps producing.

Six times across four review rounds a rule was applied at one call site and not
at its sibling -- a keyword passed here and not there. Every one passed the full
suite. This removes each cross-module keyword in turn and reports the ones
nothing notices.

Two lessons from the first attempt are built in. Results are written as they are
produced, because the first run crashed after thirty minutes and printed nothing.
And each run is bounded, because one mutation made the suite HANG rather than
fail -- a hang is reported as its own outcome, since a suite that hangs gives a
developer no signal at all.
"""
import ast
import pathlib
import subprocess
import sys

PKG = pathlib.Path(__file__).resolve().parents[1] / "jsonl_otlp_exporter"
OUT = pathlib.Path("wiring-sweep-results.txt")
SKIP = {"file", "encoding", "errors", "default", "dir_fd", "key", "reverse"}
PER_RUN_SECONDS = 90


def wirings():
    for path in sorted(PKG.glob("*.py")):
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg is None or kw.arg in SKIP:
                    continue
                seg = ast.get_source_segment(source, kw)
                if seg:
                    yield path, kw.lineno, seg


def run_suite():
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q", "-x"],
            capture_output=True, text=True, timeout=PER_RUN_SECONDS)
        return "SURVIVED" if r.returncode == 0 else "caught"
    except subprocess.TimeoutExpired:
        return "HUNG"


seen = set()
lines = []
with OUT.open("w", encoding="utf-8") as log:
    for path, lineno, seg in wirings():
        key = (path.name, seg)
        if key in seen:
            continue
        seen.add(key)
        original = path.read_text()
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
        path.write_text(mutated)
        try:
            verdict = run_suite()
        finally:
            path.write_text(original)
        line = f"{verdict:9} {path.name}:{lineno}  {seg}"
        log.write(line + "\n")
        log.flush()
        print(line, flush=True)

print("\n=== summary ===", flush=True)
