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
    depending on how the argv was built. A path outside the repo is returned
    as its absolute form; nothing here rejects it, because the real guard is the
    rule's repo-relative `paths.include`, which cannot match such a file.
    """
    path = Path(reported)
    if not path.is_absolute():
        path = REPO_ROOT / path
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def scan_all(targets: list[Path]) -> dict[str, list[dict]]:
    """Run the rule over every target in ONE semgrep process.

    Findings keyed by repo-relative path, for exactly the targets semgrep
    reports as scanned. A target absent from the returned mapping did not match
    the rule's `paths.include`, and callers must treat that as a failure: zero
    findings is ambiguous on its own, meaning both "the rule applied and the
    file is clean" and "the rule's paths.include excluded the file entirely".

    What `paths.scanned` membership does NOT prove is that the file parsed.
    Measured on semgrep 1.166.0: an unparseable target is still listed as
    scanned, with exit 0, empty stderr, and empty `errors` and `skipped` arrays
    — there is no signal to gate on. So a ratcheted script that stops parsing
    reads as clean here. That hole predates batching and is unchanged by it;
    tracked as `sast-semgrep-unparseable-target-reads-clean` in
    `workspace.toml [backlog].open`.

    One process, not one per target, because semgrep's startup dominates its work
    on inputs this small — five invocations over five small files spent several
    times longer than one invocation over all of them (measured figures in
    docs/specs/semgrep-selftest-batching/spec.md, deliberately not restated here
    so they cannot drift). Merging them is safe in a way that batching `pip-audit` was
    not (see docs/specs/pip-audit-batching/spec.md): `paths.include` filtering,
    `--max-target-bytes`, `nosemgrep`, and the per-path timeout are all applied
    per file, so no per-file verdict can change, and semgrep names the file in
    every finding, so attribution survives the merge natively instead of having
    to be reconstructed.
    """
    if not targets:
        # Semgrep with no target argument walks the working directory, and this
        # rule's paths.include would then match the same five files anyway — so
        # an empty argv yields a green run that proved nothing about the argv.
        raise RuntimeError("scan_all called with no targets — refusing to let semgrep walk the repo")
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
        listed = ", ".join(_key(t) for t in targets)
        raise RuntimeError(f"semgrep produced no output for [{listed}] — stderr: {proc.stderr}")
    payload = json.loads(proc.stdout)
    findings: dict[str, list[dict]] = {
        _key(path): [] for path in payload.get("paths", {}).get("scanned", [])
    }
    for hit in payload["results"]:
        key = _key(hit["path"])
        if key not in findings:
            # A finding on a path semgrep did not list as scanned means the two
            # halves of its own report disagree. Raise rather than create the
            # key, which would hand a caller findings for an unscanned file.
            raise RuntimeError(f"semgrep reported a finding in unscanned {key}")
        findings[key].append(hit)
    return findings


def unrequested(targets: list[Path], findings: dict[str, list[dict]]) -> list[str]:
    """Scanned paths nobody asked for — i.e. semgrep widened the argv.

    The complement (a requested target that was *not* scanned) is left to
    `hits_for`, which can name the failing case; this half has no test name to
    attach to, so it is reported once from `main`.

    Deliberately NOT a proof that the target argv is load-bearing, and measured
    not to be: strip the target arguments and semgrep walks the working
    directory instead, where this rule's `paths.include` rediscovers exactly the
    same five files — same verdict, nothing extra, so this check cannot fire.
    The rule's `paths.include` is the authoritative scope; the target list is
    redundant with it by construction. This stays as defence in depth for the
    case where the two diverge — a new file dropped into the fixtures directory,
    which the glob would match and nobody requested.
    """
    return sorted(set(findings) - {_key(t) for t in targets})


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

    # Guard the fixtures explicitly, the way test_fixed_scripts_silent guards its
    # own subjects. Without this a renamed fixture is dropped from the argv and
    # the only diagnosis is hits_for's "check paths.include in the rule", which
    # points at the rule when the file is simply gone.
    missing = [p for p in (FIXTURES / "positive.py", FIXTURES / "negative.py") if not p.is_file()]
    for path in missing:
        fail(f"{path.name} fixture is present", f"fixture not found at {path} — path drifted?")
    if missing:
        print(f"\n{ran - len(failures)}/{ran} passed")
        print("Failed:", ", ".join(failures), file=sys.stderr)
        return 1

    targets = [FIXTURES / "positive.py", FIXTURES / "negative.py", *FIXED_SCRIPTS]
    findings = scan_all([t for t in targets if t.is_file()])

    extra = unrequested([t for t in targets if t.is_file()], findings)
    if extra:
        fail("semgrep scanned only the requested targets", f"also scanned {extra}")

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
