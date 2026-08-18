#!/usr/bin/env python3
"""Self-test for tools/semgrep/argv-path-boundary.yml.

The rule is excluded from `make sast`'s scan of its own fixtures (see
SEMGREP_EXCLUDE in the Makefile), so without this file the fixtures would be
dead weight and the rule would be unproven. This is the gate that keeps them
honest.

Asserts five things:
  1. The rule FIRES on the pre-fix shape (positive fixture) — a rule that
     never fires is indistinguishable from no rule at all.
  2. The rule is SILENT on both post-fix shapes (negative fixture): the
     `_validated_root(...)` validator, and the pre-existing
     resolve()-then-is_relative_to() exemplar from check-spec-status.py.
  3. The rule is SILENT on the three production scripts it is scoped to,
     i.e. the fix actually satisfies it.
  4. Both fixtures are present, so a renamed one is diagnosed rather than
     dropped from the scan.
  5. No fixture file sits in the fixtures directory unscanned — the rule's
     `paths.include` covers that directory by glob, but semgrep only scans the
     files it is named.

All five run in ONE semgrep process; see `scan_all` for why that is safe.

**What a green result here does and does not mean.** It means the rule's
`paths.include` matched each target and the rule's verdict on it was as
expected. It does NOT mean the target parsed: a whole-file parse failure is
reported as scanned-with-no-findings and no error, so a ratcheted script that
stops parsing reads as clean (see `scan_all`, and the
`sast-semgrep-unparseable-target-reads-clean` backlog entry). Nor does it prove
the boundary is validated — see the rule's own header, which is emphatic that it
is a tripwire for the obvious regression, not a proof of correctness.

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

# PyYAML, not stdlib. Deliberate, and safe in the one place this file runs:
# `make sast` (Makefile), which the module docstring explains is the only
# invocation because the test needs semgrep on PATH. That target's CI job
# installs tools/requirements-sast.txt, whose `bandit` requires `PyYAML>=5.3.1`,
# so the import resolves there; pyyaml is also declared directly in
# tools/requirements.txt for local runs. The alternative — regex-scraping
# `paths.include` out of the rule file — is the re-implement-a-YAML-parser
# antipattern that produced five of six review rounds against
# tools/test-build-check-workflow.py (see
# `ci-gate-parallelization-posture-test-yaml-parser` in workspace.toml).
import yaml

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
RULE = REPO_ROOT / "tools" / "semgrep" / "argv-path-boundary.yml"
FIXTURES = REPO_ROOT / "tools" / "semgrep" / "fixtures" / "argv-path-boundary"

# The rule under test, parsed once. `--config` names a FILE, so a finding's
# check_id is `<file-stem>.<rule-id>`; RULE_ID is the bare id used to filter.
RULE_ID = "argv-path-without-boundary-validator"


def ratcheted_scope() -> tuple[list[Path], list[str]]:
    """Split the rule's own `paths.include` into (concrete files, glob patterns).

    THE RULE FILE IS THE ONLY SCOPE DEFINITION. This used to be a FIXED_SCRIPTS
    constant that restated `paths.include`, with nothing reconciling the two, and
    the direction that can drift silently is the one that was unchecked: a list
    SHORTER than the rule's scope leaves a ratcheted script unscanned while every
    assertion still passes.

    That was not hypothetical. Measured on the commit this function replaced:
      * `_loop_guards.py` had been added to `paths.include` and never to
        FIXED_SCRIPTS, so it was never a scan target and never asserted silent.
      * Setting `FIXED_SCRIPTS = []` printed "2/2 passed" and exited 0 — the
        entire production half of the ratchet proving nothing, with `make sast`
        green.

    Deriving the list makes both impossible: a path in the rule is a path this
    test scans and asserts, and `test_ratcheted_scope_is_covered` fails by name
    if semgrep did not report one as scanned.
    """
    document = yaml.safe_load(RULE.read_text(encoding="utf-8"))
    rules = document.get("rules") or []
    if len(rules) != 1:
        # Not a style objection: the check_id filter below names ONE rule, and
        # `paths.include` is per-rule. A second rule would need its own scope
        # read and its own assertions, so fail loudly rather than silently
        # ratchet against the first one only.
        raise RuntimeError(
            f"{RULE.name}: expected exactly 1 rule, found {len(rules)} — "
            "this self-test's scope derivation and check_id filter both assume one"
        )
    include = rules[0].get("paths", {}).get("include") or []
    if not include:
        raise RuntimeError(f"{RULE.name}: rule declares no paths.include — nothing is ratcheted")
    concrete = [REPO_ROOT / entry for entry in include if "*" not in entry]
    globs = [entry for entry in include if "*" in entry]
    if not concrete:
        # Every entry a glob would mean no production script is ratcheted, which
        # is the fail-open state this function exists to make impossible.
        raise RuntimeError(
            f"{RULE.name}: paths.include has no concrete file entries — "
            f"only globs {globs!r}; no production script would be asserted"
        )
    return concrete, globs


# NOT called at import time, deliberately. main() returns 0 with a `skip:` line
# when semgrep is absent, matching `make sast`'s optional-tool posture; a
# module-level call would turn a malformed rule file into exit 1 on a machine
# with no semgrep, which is a behaviour change this fix has no business making.

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

    What `paths.scanned` membership does NOT prove is that the file parsed, and
    the signal available depends on how it failed. Measured on semgrep 1.166.0:
    a *partial* parse failure (an unbalanced bracket, a nonsense token) does
    surface as a path-attributed `PartialParsing` entry in `errors`, which
    `--strict` escalates to exit 3 — gateable. But a whole-file or whole-construct
    failure (`def broken(:`, `3 = x`) yields empty `errors`, empty `skipped`,
    empty stderr and exit 0 even under `--strict` — nothing to gate on. So a
    ratcheted script can still stop parsing and read as clean here. The residue
    predates batching and is unchanged by it; tracked as
    `sast-semgrep-unparseable-target-reads-clean` in `workspace.toml`.

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
            # `--` so a future fixture or ratcheted script whose name begins with
            # `-` is scanned rather than silently consumed as a flag.
            "--",
            *(str(t) for t in targets),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        cwd=str(REPO_ROOT),
        # A wedged semgrep must fail the gate, not hang it. Batching concentrates
        # all five targets behind this one process, so there is no partial result
        # to fall back on. Generous relative to the ~10s this normally takes.
        timeout=300,
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
            # Checked before the rule filter: an inconsistent report is a defect
            # whichever rule produced the finding.
            raise RuntimeError(f"semgrep reported a finding in unscanned {key}")
        # Key on the RULE, not just the file. `--config` names a file, so every
        # rule in argv-path-boundary.yml lands in these results. Grouping by path
        # alone means a second rule in that file — or a replacement one — could
        # satisfy the positive-fixture proof-of-life while
        # argv-path-without-boundary-validator itself is neutered. `ratcheted_scope`
        # refuses a multi-rule file, so today this filter is belt to that brace;
        # keep both, because the failure it prevents is a green ratchet.
        if not hit["check_id"].endswith(RULE_ID):
            continue
        findings[key].append(hit)
    return findings


def unwired_fixtures(targets: list[Path]) -> list[str]:
    """Fixture files this run would not scan.

    The rule's `paths.include` covers the whole fixtures directory by glob, but
    semgrep only ever scans the files it is *named* — an explicit file argv is
    never widened to siblings (measured on 1.166.0). So a fixture added to that
    directory and not added to the target list below is silently unexercised: the
    glob suggests it is covered, and nothing scans it.

    This replaced an earlier `unrequested()` check that compared the scanned set
    against the requested set. That check could not fire in any configuration —
    semgrep neither widens an explicit file argv (so nothing extra ever appears)
    nor, when the argv is stripped entirely, returns anything but the same five
    files this rule's `paths.include` selects. Enumerating the directory is the
    form that actually guards the risk the old docstring claimed to.
    """
    named = {t.resolve() for t in targets}
    return sorted(p.name for p in FIXTURES.glob("*.py") if p.resolve() not in named)


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


def test_ratcheted_scope_is_covered(
    findings: dict[str, list[dict]], ratcheted: list[Path]
) -> None:
    """Every concrete `paths.include` entry was requested AND reported scanned.

    This is the assertion that makes the derived scope load-bearing rather than
    decorative. `test_ratcheted_scripts_silent` proves each file has no findings;
    without this one, "no findings" would still be satisfiable by semgrep never
    having looked — which is precisely how a shrinking target list used to pass.
    """
    name = "every ratcheted path in the rule was scanned"
    missing = [_key(script) for script in ratcheted if _key(script) not in findings]
    if missing:
        fail(
            name,
            f"in the rule's paths.include but not reported scanned: {missing}. "
            "Either the path no longer exists, or semgrep declined it — both leave "
            "that file unratcheted while its silence reads as clean.",
        )
    else:
        ok(name)


def test_ratcheted_scripts_silent(
    findings: dict[str, list[dict]], ratcheted: list[Path]
) -> None:
    for script in ratcheted:
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
    ratcheted, _globs = ratcheted_scope()

    missing = [p for p in (FIXTURES / "positive.py", FIXTURES / "negative.py") if not p.is_file()]
    for path in missing:
        fail(f"{path.name} fixture is present", f"fixture not found at {path} — path drifted?")
    if missing:
        print(f"\n{ran - len(failures)}/{ran} passed")
        print("Failed:", ", ".join(failures), file=sys.stderr)
        return 1

    targets = [FIXTURES / "positive.py", FIXTURES / "negative.py", *ratcheted]
    present = [t for t in targets if t.is_file()]

    unwired = unwired_fixtures(present)
    if unwired:
        fail("every fixture is wired into the scan", f"never scanned: {unwired}")

    findings = scan_all(present)

    test_positive_fixture_fires(findings)
    test_negative_fixture_silent(findings)
    test_ratcheted_scope_is_covered(findings, ratcheted)
    test_ratcheted_scripts_silent(findings, ratcheted)

    total = ran
    passed = total - len(failures)
    print(f"\n{passed}/{total} passed")
    if failures:
        print("Failed:", ", ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
