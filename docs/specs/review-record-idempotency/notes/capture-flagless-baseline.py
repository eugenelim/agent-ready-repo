#!/usr/bin/env python3
"""Capture how `loop-cohort review record` behaves with no `--operation-id`.

This is the comparison value for the spec's "unchanged for a caller that omits
the flag" criterion. It must be captured and committed BEFORE `cmd_review_record`
changes, because a baseline regenerated afterwards would compare the changed
writer against itself.

Records, per recording form: the command's exit code, its normalised stdout line,
and the delta over the six review fields. Not the whole `state.json` — the
template gains fields during this delivery, so a whole-file comparison could
never pass afterwards.

Run from the repository root. Writes `flagless-baseline.json` beside this file.
Re-running against an unchanged writer must reproduce the file byte for byte.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "packs/core/.apm/skills/work-loop/scripts"
# `.context/` is gitignored, so the throwaway spec directories never enter git.
# A per-process subdirectory below it, rather than one fixed path: the roster
# test drives this script, and a fixed path lets a concurrent run in the same
# worktree delete the directory a live run is mid-way through writing.
SCRATCH_PARENT = ROOT / ".context"

# The six fields a recording round mutates. The delta over these is the contract;
# everything else in `state.json` is out of scope for this comparison.
REVIEW_FIELDS = (
    "review_round_count",
    "review_retry_count",
    "finding_fingerprints",
    "previous_finding_fingerprints",
    "last_review_clean_source",
    "last_review_clean_digest",
)

CLEAN_SENTINEL = "Clean — ready to commit."
FP_A = "a" * 64
FP_B = "b" * 64

SPEC_BODY = """# Spec: baseline

- **Status:** Approved

## Acceptance Criteria

- [ ] AC1
"""

PLAN_BODY = """# Plan: baseline

- **Status:** Approved

### T1: only task

**Depends on:** none

**Tests:**
- none

**Approach:**
- none

**Done when:** never run.
"""

ADJUDICATION = f"""## Main-loop result

{CLEAN_SENTINEL}

## Refuted audit

None.

## Indeterminate audit

None.
"""


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], capture_output=True, text=True, cwd=ROOT
    )


def normalise(text: str, run_id: str, feature: str, scratch: Path) -> str:
    """Strip the values that differ between two runs of the same capture.

    The scratch directory is normalised first and by longest match: its name now
    carries a per-process random suffix, and the writer echoes the spec-dir path
    back in its messages, so leaving it in would make the baseline differ from
    itself on every run.
    """
    for path in sorted((str(scratch), str(scratch.relative_to(ROOT))), key=len,
                       reverse=True):
        text = text.replace(path, "<scratch>")
    text = text.replace(run_id, "<run-id>").replace(feature, "<feature>")
    text = re.sub(r"\b[0-9a-f]{64}\b", "<sha256>", text)
    text = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
                  "<uuid>", text)
    return text.strip()


def review_fields(state_path: Path) -> dict[str, object]:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    return {k: state.get(k) for k in REVIEW_FIELDS}


def delta(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    return {k: {"from": before[k], "to": after[k]} for k in REVIEW_FIELDS
            if before[k] != after[k]}


def capture(scratch: Path, form_name: str, extra_argv: list[str],
            files: dict[str, str]) -> dict:
    feature = f"baseline-{form_name}"
    spec_dir = scratch / feature
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text(SPEC_BODY, encoding="utf-8")
    (spec_dir / "plan.md").write_text(PLAN_BODY, encoding="utf-8")
    for name, body in files.items():
        (spec_dir / name).write_text(body, encoding="utf-8")

    rel = str(spec_dir.relative_to(ROOT))
    init = run(str(SCRIPTS / "loop-engine.py"), "init", rel, "--mode", "code", "--json")
    if init.returncode != 0:
        raise SystemExit(f"{form_name}: engine init failed: {init.stderr}")
    run_id = json.loads(init.stdout)["run_id"]
    coh = run(str(SCRIPTS / "loop-cohort.py"), "init", rel, "--run-id", run_id)
    if coh.returncode != 0:
        raise SystemExit(f"{form_name}: cohort init failed: {coh.stderr}")

    state_path = spec_dir / "state.json"
    before = review_fields(state_path)
    argv = [str(SCRIPTS / "loop-cohort.py"), "review", "record", rel,
            *[a.replace("<spec-dir>", rel) for a in extra_argv],
            "--expect-run-id", run_id]
    proc = run(*argv)
    after = review_fields(state_path)

    return {
        "exit_code": proc.returncode,
        "stdout": normalise(proc.stdout, run_id, feature, scratch),
        "stderr": normalise(proc.stderr, run_id, feature, scratch),
        "delta": delta(before, after),
    }


def main(argv: list[str] | None = None) -> int:
    """Default is `--verify`; `--capture` is the only mode that writes.

    Writing by default would let anyone "regenerate the baseline" and silently
    replace the pre-change oracle with post-change output, which is the one thing
    this artifact exists to prevent.
    """
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", default=True,
                      help="compare the current writer against the committed baseline")
    mode.add_argument("--capture", action="store_true",
                      help="overwrite the baseline; only valid before the writer changes")
    args = parser.parse_args(argv)

    SCRATCH_PARENT.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="flagless-baseline-", dir=SCRATCH_PARENT))
    forms = {
        "fingerprint": (["--fingerprint", FP_A, "--fingerprint", FP_B], {}),
        "direct-clean-file": (
            ["--direct-clean-file", "<spec-dir>/clean.md"],
            {"clean.md": CLEAN_SENTINEL},
        ),
        "report-adjudication": (
            ["--report", "<spec-dir>/adjudication.md", "--adjudication"],
            {"adjudication.md": ADJUDICATION},
        ),
        "all-skipped": (["--all-skipped"], {}),
    }
    baseline = {
        "_note": (
            "Captured from the unchanged `cmd_review_record`, before "
            "`--operation-id` existed. Regenerating this from the changed writer "
            "would compare it against itself and prove nothing."
        ),
        "review_fields": list(REVIEW_FIELDS),
        "forms": {name: capture(scratch, name, argv, files)
                  for name, (argv, files) in forms.items()},
    }
    out = Path(__file__).resolve().parent / "flagless-baseline.json"
    rendered = json.dumps(baseline, indent=2, ensure_ascii=False) + "\n"
    shutil.rmtree(scratch, ignore_errors=True)

    if args.capture:
        out.write_text(rendered, encoding="utf-8")
        print(f"captured {out.relative_to(ROOT)}")
        return 0

    committed = json.loads(out.read_text(encoding="utf-8"))
    drift = [name for name, rec in baseline["forms"].items()
             if committed["forms"].get(name) != rec]
    for name, rec in baseline["forms"].items():
        mark = "DRIFT" if name in drift else "ok   "
        print(f"  {mark} {name:22s} exit={rec['exit_code']} "
              f"changed={sorted(rec['delta'])}")
    if drift:
        print(f"\nflagless behaviour changed for: {', '.join(drift)}")
        return 1
    print("\nflagless behaviour matches the committed baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
