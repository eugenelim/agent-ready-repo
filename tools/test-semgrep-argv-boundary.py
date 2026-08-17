#!/usr/bin/env python3
"""Self-test for tools/semgrep/argv-path-boundary.yml.

The rule is excluded from `make sast`'s scan of its own fixtures (see
SEMGREP_EXCLUDE in the Makefile), so without this file the fixtures would be
dead weight and the rule would be unproven. This is the gate that keeps them
honest.

Asserts three things:
  1. The rule FIRES on the pre-fix shape (positive fixture) — a rule that
     never fires is indistinguishable from no rule at all.
  2. The rule is SILENT on both post-fix shapes (negative fixture): the
     `_validated_root(...)` validator, and the pre-existing
     resolve()-then-is_relative_to() exemplar from check-spec-status.py.
  3. The rule is SILENT on the three production scripts it is scoped to,
     i.e. the fix actually satisfies it.

Run: python3 tools/test-semgrep-argv-boundary.py
Exit 0 = all pass; exit non-zero = at least one failure. Skips (exit 0) when
semgrep is not installed, matching `make sast`'s optional-tool posture.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
RULE = REPO_ROOT / "tools" / "semgrep" / "argv-path-boundary.yml"
FIXTURES = REPO_ROOT / "tools" / "semgrep" / "fixtures" / "argv-path-boundary"

SCRIPTS_DIR = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts"
FIXED_SCRIPTS = [
    SCRIPTS_DIR / "lint-traceability.py",
    SCRIPTS_DIR / "lint-spec-status.py",
    SCRIPTS_DIR / "loop-cohort.py",
]

failures: list[str] = []
ran = 0


def ok(name: str) -> None:
    global ran
    ran += 1
    print(f"ok   [{name}]")


def fail(name: str, reason: str) -> None:
    global ran
    ran += 1
    failures.append(name)
    print(f"FAIL [{name}]: {reason}", file=sys.stderr)


def _key(reported: str | Path) -> str:
    """Normalise a path to a repo-relative POSIX key.

    Both sides of the lookup go through this. Semgrep echoes paths back in
    whichever form it was handed — an absolute argument yields absolute
    `paths.scanned` entries, a relative one yields relative — so normalising
    both the targets and the reported paths keeps the mapping from silently
    depending on how the argv was built. Paths outside the repo are returned
    as-is, which simply will not match a target and therefore fails closed.
    """
    path = Path(reported)
    if not path.is_absolute():
        path = REPO_ROOT / path
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def scan_all(targets: list[Path]) -> dict[str, list[dict]]:
    """Run the rule over every target in ONE semgrep process.

    Findings keyed by repo-relative path, restricted to the targets semgrep
    reports as actually scanned. A target absent from the returned mapping was
    NOT scanned, and callers must treat that as a failure: zero findings is an
    ambiguous result on its own, meaning both "the rule ran and the file is
    clean" and "the rule's paths.include excluded the file entirely".

    One process, not one per target, because semgrep has a ~7.4s startup floor
    and these targets are five small files — five invocations spent ~29.8s to do
    ~9s of work. Merging them is safe in a way that batching `pip-audit` was
    not (see docs/specs/pip-audit-batching/spec.md): semgrep parses and matches
    each file independently, so no per-file verdict can change, and it names the
    file in every finding, so attribution survives the merge natively instead of
    having to be reconstructed.
    """
    proc = subprocess.run(
        [
            "semgrep", "--config", str(RULE),
            "--json", "--quiet", "--metrics", "off",
            *(str(t) for t in targets),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        cwd=str(REPO_ROOT),
    )
    if not proc.stdout.strip():
        raise RuntimeError(
            f"semgrep produced no output for {len(targets)} targets — stderr: {proc.stderr}"
        )
    payload = json.loads(proc.stdout)
    findings: dict[str, list[dict]] = {
        _key(path): [] for path in payload.get("paths", {}).get("scanned", [])
    }
    for hit in payload["results"]:
        # A finding on a path semgrep did not list as scanned would mean the two
        # halves of its own report disagree; surface that rather than swallow it.
        findings.setdefault(_key(hit["path"]), []).append(hit)
    return findings


def hits_for(name: str, target: Path, findings: dict[str, list[dict]]) -> list[dict] | None:
    """Findings for `target`, or None (having failed `name`) if it wasn't scanned.

    Every assertion goes through here so that "semgrep never looked at this
    file" can never read as "this file is clean" — including for the fixtures,
    which the per-invocation version did not check. Batching makes the check
    necessary for them too: findings now arrive keyed by path, so a key that
    never matches yields an empty list and would pass a zero-findings assertion
    without the rule having examined anything.
    """
    key = _key(target)
    if key not in findings:
        fail(name, f"rule did not scan {key} — check paths.include in the rule")
        return None
    return findings[key]


def test_positive_fixture_fires(findings: dict[str, list[dict]]) -> None:
    name = "positive fixture fires exactly once"
    hits = hits_for(name, FIXTURES / "positive.py", findings)
    if hits is None:
        return
    if len(hits) != 1:
        fail(name, f"expected 1 finding, got {len(hits)}: {[h['start']['line'] for h in hits]}")
    else:
        ok(name)


def test_negative_fixture_silent(findings: dict[str, list[dict]]) -> None:
    name = "negative fixture is silent (validator + is_relative_to exemplar)"
    hits = hits_for(name, FIXTURES / "negative.py", findings)
    if hits is None:
        return
    if hits:
        lines = [h["start"]["line"] for h in hits]
        fail(name, f"expected 0 findings, got {len(hits)} at lines {lines}")
    else:
        ok(name)


def test_fixed_scripts_silent(findings: dict[str, list[dict]]) -> None:
    for script in FIXED_SCRIPTS:
        name = f"{script.name} is silent after the fix"
        if not script.is_file():
            fail(name, f"subject not found at {script} — path drifted?")
            continue
        # Order matters: prove the rule REACHED the file before trusting its
        # silence. Dropping this path from the rule's paths.include also
        # yields zero findings, so a findings-only assertion would stay green
        # while the ratchet covered nothing.
        hits = hits_for(name, script, findings)
        if hits is None:
            continue
        if hits:
            lines = [h["start"]["line"] for h in hits]
            fail(name, f"expected 0 findings, got {len(hits)} at lines {lines}")
        else:
            ok(name)


def main() -> int:
    if shutil.which("semgrep") is None:
        print("skip: semgrep not on PATH (install: pip install -r tools/requirements-sast.txt)")
        return 0
    if not RULE.is_file():
        print(f"FAIL: rule not found at {RULE}", file=sys.stderr)
        return 1

    targets = [FIXTURES / "positive.py", FIXTURES / "negative.py", *FIXED_SCRIPTS]
    findings = scan_all([t for t in targets if t.is_file()])

    test_positive_fixture_fires(findings)
    test_negative_fixture_silent(findings)
    test_fixed_scripts_silent(findings)

    total = ran
    passed = total - len(failures)
    print(f"\n{passed}/{total} passed")
    if failures:
        print("Failed:", ", ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
