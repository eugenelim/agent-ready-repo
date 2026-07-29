#!/usr/bin/env python3
"""Phase 3 readiness gate for the Atlassian end-to-end retrofit.

Runs or consumes existing validators across five areas and reports whether
the repository meets every prerequisite for the Phase 3 Atlassian retrofit.

Exit codes:
  0  — all required checks pass
  1  — one or more required checks fail or are unverified

Usage:
  python3 tools/check-atlassian-phase3-readiness.py          # human-readable output
  python3 tools/check-atlassian-phase3-readiness.py --json   # machine-readable JSON

This command is an orchestration and evidence tool, NOT a source of product
doctrine. It verifies what the repository's existing validators and sources
already declare. Add checks here only when a validator or source already exists.

Note: This command is a MILESTONE tool, not a permanent global gate. It may
contain phase-specific checks (Phase 2C status) that do not belong in the
everyday build-check pipeline. See docs/specs/phase2e-convergence/spec.md.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

# ── repository root ────────────────────────────────────────────────────────────


def _root() -> pathlib.Path:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return pathlib.Path(r.stdout.strip())
    except FileNotFoundError:
        pass
    return pathlib.Path.cwd()


ROOT = _root()
PY = sys.executable


# ── check result type ──────────────────────────────────────────────────────────

def _check(
    check_id: str,
    *,
    status: str,        # "pass" | "fail" | "skipped" | "unverified"
    evidence: list[str],
) -> dict:
    return {"id": check_id, "status": status, "evidence": evidence}


def _run_validator(cmd: list[str]) -> tuple[bool, str]:
    """Run a tool; return (passed, output_excerpt)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=ROOT)
        passed = r.returncode == 0
        out = (r.stdout + r.stderr).strip()
        return passed, out[:400] if len(out) > 400 else out
    except FileNotFoundError as exc:
        return False, f"command not found: {exc}"


def _head(path: pathlib.Path, lines: int = 5) -> str:
    try:
        text = path.read_text(encoding="utf-8")
        return "\n".join(text.splitlines()[:lines])
    except FileNotFoundError:
        return "<not found>"


def _contains(path: pathlib.Path, substring: str) -> bool:
    try:
        return substring in path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False


def _exists(path: pathlib.Path) -> bool:
    return path.exists()


# ── Area A: Product Documentation identity ────────────────────────────────────

def check_product_documentation_canonical() -> dict:
    """product-documentation pack exists and is canonical."""
    pack_toml = ROOT / "packs" / "product-documentation" / "pack.toml"
    skill_dir = (
        ROOT / "packs" / "product-documentation" / ".apm" / "skills" / "author-product-docs"
    )
    evidence = []
    ok = True

    if _exists(pack_toml):
        evidence.append(f"pack.toml present: {pack_toml.relative_to(ROOT)}")
    else:
        evidence.append(f"MISSING: {pack_toml.relative_to(ROOT)}")
        ok = False

    if _exists(skill_dir):
        evidence.append(f"author-product-docs skill present: {skill_dir.relative_to(ROOT)}")
    else:
        evidence.append(f"MISSING: {skill_dir.relative_to(ROOT)}")
        ok = False

    return _check("product-documentation-canonical", status="pass" if ok else "fail",
                  evidence=evidence)


def check_compatibility_pack_deprecated() -> dict:
    """user-guide-diataxis is deprecated, contains no competing implementation."""
    pack_toml = ROOT / "packs" / "user-guide-diataxis" / "pack.toml"
    new_guide = (
        ROOT / "packs" / "user-guide-diataxis" / ".apm" / "skills" / "new-guide" / "SKILL.md"
    )
    evidence = []
    ok = True

    if not _exists(pack_toml):
        return _check("compatibility-pack-deprecated", status="fail",
                      evidence=["MISSING: packs/user-guide-diataxis/pack.toml"])

    if _contains(pack_toml, "Deprecated compatibility"):
        evidence.append("pack.toml description marks pack as deprecated")
    else:
        evidence.append("WARN: pack.toml description does not say 'Deprecated compatibility'")

    skill_dir = ROOT / "packs" / "user-guide-diataxis" / ".apm" / "skills"
    if skill_dir.exists():
        skills = [d.name for d in skill_dir.iterdir() if d.is_dir()]
        evidence.append(f"skills in compat pack: {skills} (expected: ['new-guide'] only)")
        if skills != ["new-guide"]:
            evidence.append("FAIL: more than one skill in compat pack")
            ok = False

    if _exists(new_guide):
        shim_text = new_guide.read_text(encoding="utf-8")
        if "author-product-docs" in shim_text:
            evidence.append("new-guide SKILL.md routes to author-product-docs (confirmed shim)")
        else:
            evidence.append("FAIL: new-guide SKILL.md does not route to author-product-docs")
            ok = False
    else:
        evidence.append("MISSING: new-guide/SKILL.md")
        ok = False

    # No quadrant seeds
    seeds_dir = ROOT / "packs" / "user-guide-diataxis" / ".apm" / "seeds"
    if seeds_dir.exists():
        evidence.append("FAIL: compat pack has a seeds/ directory (must not)")
        ok = False
    else:
        evidence.append("No seeds/ directory in compat pack")

    return _check("compatibility-pack-deprecated", status="pass" if ok else "fail",
                  evidence=evidence)


def check_site_grouping_canonical() -> dict:
    """site.toml places product-documentation in 'Content and design'."""
    site_toml = ROOT / "site.toml"
    evidence = []
    ok = True

    if not _exists(site_toml):
        return _check("site-grouping-canonical", status="fail",
                      evidence=["MISSING: site.toml"])

    text = site_toml.read_text(encoding="utf-8")
    if "product-documentation" in text:
        # Find the group
        lines = text.splitlines()
        in_content_design = False
        found_pd = False
        for line in lines:
            if "Content and design" in line:
                in_content_design = True
            if in_content_design and "product-documentation" in line:
                found_pd = True
                break
            if in_content_design and line.strip().startswith("[[groups]]"):
                in_content_design = False

        if found_pd:
            evidence.append("product-documentation is in 'Content and design' group in site.toml")
        else:
            evidence.append("FAIL: product-documentation not found in 'Content and design' group")
            ok = False
    else:
        evidence.append("FAIL: product-documentation absent from site.toml")
        ok = False

    if "user-guide-diataxis" not in text:
        evidence.append("user-guide-diataxis absent from site.toml (correct — deprecated)")
    else:
        evidence.append("WARN: user-guide-diataxis present in site.toml")

    return _check("site-grouping-canonical", status="pass" if ok else "fail",
                  evidence=evidence)


def check_guide_doctrine() -> dict:
    """guides/README.md does not teach mandatory physical quadrant directories."""
    readme = ROOT / "guides" / "README.md"
    evidence = []
    ok = True

    if not _exists(readme):
        return _check("guide-doctrine-metadata-based", status="fail",
                      evidence=["MISSING: guides/README.md"])

    text = readme.read_text(encoding="utf-8")
    bad_patterns = ["tutorials/", "how-to/", "reference/", "explanation/"]
    # Check for mandatory quadrant directory teaching — a problem if they appear as
    # required filesystem paths
    found_mandatory = False
    for pattern in bad_patterns:
        if f"mkdir {pattern}" in text or f"create a {pattern}" in text:
            found_mandatory = True
            ok = False
            evidence.append(f"FAIL: guides/README.md teaches mandatory directory '{pattern}'")

    if not found_mandatory:
        evidence.append(
            "guides/README.md does not instruct authors to create physical quadrant dirs"
        )

    evidence.append(f"guides/README.md size: {len(text)} bytes")
    return _check("guide-doctrine-metadata-based", status="pass" if ok else "fail",
                  evidence=evidence)


# ── Area B: Journey framework ──────────────────────────────────────────────────

def check_journey_sync() -> dict:
    """Pack journey sync and parity pass."""
    passed, out = _run_validator([PY, "tools/lint-pack-journeys.py"])
    return _check("journey-pack-lint", status="pass" if passed else "fail",
                  evidence=[out or "(no output)"])


def check_journey_contract_lint() -> dict:
    """Live journey-contract lint passes."""
    passed, out = _run_validator([PY, "tools/lint-journey-contract.py"])
    return _check("journey-contract-lint", status="pass" if passed else "fail",
                  evidence=[out or "(no output)"])


def check_journey_parity() -> dict:
    """Generated journey parity passes."""
    parity_tool = ROOT / "tools" / "lint-web-journey-parity.py"
    if not parity_tool.exists():
        return _check("journey-generated-parity", status="skipped",
                      evidence=["tools/lint-web-journey-parity.py not found"])
    passed, out = _run_validator([PY, str(parity_tool)])
    return _check("journey-generated-parity", status="pass" if passed else "fail",
                  evidence=[out or "(no output)"])


def check_journey_subset_allowed() -> dict:
    """Journeys are not forced to list all pack skills (count-parity fix)."""
    lint = ROOT / "tools" / "lint-pack-journeys.py"
    if not _exists(lint):
        return _check("journey-subset-journeys-allowed", status="fail",
                      evidence=["tools/lint-pack-journeys.py not found"])

    text = lint.read_text(encoding="utf-8")
    if "skill count mismatch" in text:
        return _check("journey-subset-journeys-allowed", status="fail",
                      evidence=["lint-pack-journeys.py still enforces count parity "
                                "(skill count mismatch check present)"])
    return _check("journey-subset-journeys-allowed", status="pass",
                  evidence=["lint-pack-journeys.py uses reference validity, not count parity"])


# ── Area C: Phase 2C UI primitives ────────────────────────────────────────────

def check_phase2c_ui_primitives() -> dict:
    """Phase 2C UI primitives are implemented (component tests pass)."""
    spec = ROOT / "docs" / "specs" / "site-ui-primitives" / "spec.md"
    evidence = []

    if _exists(spec):
        text = spec.read_text(encoding="utf-8")
        # Check spec status
        for line in text.splitlines()[:10]:
            if "Status" in line:
                evidence.append(f"spec status: {line.strip()}")
                break

        unchecked = text.count("- [ ]")
        checked = text.count("- [x]")
        evidence.append(f"Acceptance Criteria: {checked} checked, {unchecked} unchecked")

        if "Implementing" in text[:500] or unchecked > 0:
            evidence.append("Phase 2C spec is not yet Shipped — primitives are not implemented")
            return _check("phase2c-ui-primitives", status="fail", evidence=evidence)
    else:
        evidence.append("docs/specs/site-ui-primitives/spec.md not found")
        return _check("phase2c-ui-primitives", status="fail", evidence=evidence)

    # Check if primitives fixture page exists
    fixture = ROOT / "web" / "src" / "pages" / "primitives-fixture.astro"
    if _exists(fixture):
        evidence.append("primitives-fixture.astro exists")
    else:
        evidence.append("MISSING: web/src/pages/primitives-fixture.astro")
        return _check("phase2c-ui-primitives", status="fail", evidence=evidence)

    return _check("phase2c-ui-primitives", status="pass", evidence=evidence)


# ── Area D: Atlassian contract ─────────────────────────────────────────────────

def check_atlassian_version_metadata() -> dict:
    """Atlassian pack version and plugin metadata agree."""
    pack_toml = ROOT / "packs" / "atlassian" / "pack.toml"
    manifest = (
        ROOT / "packs" / "atlassian" / ".apm" / "skills" / "jira-team-status" / "manifest.json"
    )
    evidence = []
    ok = True

    if _exists(pack_toml):
        text = pack_toml.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.strip().startswith("version"):
                evidence.append(f"pack.toml: {line.strip()}")
                break
    else:
        evidence.append("MISSING: packs/atlassian/pack.toml")
        ok = False

    if _exists(manifest):
        evidence.append(f"manifest.json present: {manifest.relative_to(ROOT)}")
    else:
        evidence.append(f"manifest.json not found (optional): {manifest.relative_to(ROOT)}")

    return _check("atlassian-version-metadata", status="pass" if ok else "fail",
                  evidence=evidence)


def check_atlassian_first_value() -> dict:
    """Atlassian first-value verification is team-backlog oriented."""
    pack_toml = ROOT / "packs" / "atlassian" / "pack.toml"
    evidence = []
    ok = True

    if not _exists(pack_toml):
        return _check("atlassian-first-value-team-oriented", status="fail",
                      evidence=["MISSING: packs/atlassian/pack.toml"])

    text = pack_toml.read_text(encoding="utf-8")
    team_phrases = ["team atlas", "team backlog", "team can work on", "read-only"]
    found = [p for p in team_phrases if p in text.lower()]
    if found:
        evidence.append(f"first-value fields use team-oriented language: {found}")
    else:
        evidence.append("FAIL: first-value fields lack team-oriented language")
        ok = False

    personal_phrases = ["list my issues", "my tickets", "my open issues"]
    bad = [p for p in personal_phrases if p in text.lower()]
    if bad:
        evidence.append(f"FAIL: first-value uses personal/individual phrases: {bad}")
        ok = False
    else:
        evidence.append("No personal/individual phrases in first-value fields")

    return _check("atlassian-first-value-team-oriented", status="pass" if ok else "fail",
                  evidence=evidence)


def check_atlassian_team_status_read_only() -> dict:
    """jira-team-status is read-only."""
    skill = ROOT / "packs" / "atlassian" / ".apm" / "skills" / "jira-team-status" / "SKILL.md"
    evidence = []
    ok = True

    if not _exists(skill):
        return _check("atlassian-team-status-read-only", status="fail",
                      evidence=["MISSING: jira-team-status/SKILL.md"])

    text = skill.read_text(encoding="utf-8")
    if "read-only" in text.lower():
        evidence.append("jira-team-status SKILL.md declares read-only operation")
    else:
        evidence.append("FAIL: 'read-only' not found in jira-team-status SKILL.md")
        ok = False

    if "don't change protected fields" in text.lower() or "not change" in text.lower():
        evidence.append("Protected-field protection declared")
    else:
        evidence.append("WARN: protected-field protection not explicitly declared in Don't rules")

    if "silently truncate" in text.lower() or "paginate" in text.lower():
        evidence.append("Pagination/completeness disclosure declared")
    else:
        evidence.append("WARN: pagination or completeness disclosure not found")

    return _check("atlassian-team-status-read-only", status="pass" if ok else "fail",
                  evidence=evidence)


def check_atlassian_story_triage_draft_only() -> dict:
    """jira-story-triage is draft-only by default."""
    skill = ROOT / "packs" / "atlassian" / ".apm" / "skills" / "jira-story-triage" / "SKILL.md"
    evidence = []
    ok = True

    if not _exists(skill):
        return _check("atlassian-story-triage-draft-only", status="fail",
                      evidence=["MISSING: jira-story-triage/SKILL.md"])

    text = skill.read_text(encoding="utf-8")
    if "read-only by default" in text.lower():
        evidence.append("jira-story-triage declares 'read-only by default'")
    else:
        evidence.append("FAIL: 'read-only by default' not in jira-story-triage SKILL.md")
        ok = False

    if "jira was not changed" in text.lower():
        evidence.append("Explicit 'Jira was not changed' confirmation declared in output")
    else:
        evidence.append("FAIL: 'Jira was not changed' confirmation not found")
        ok = False

    if "jira: update-issue" in text:
        evidence.append("Writes route to canonical jira: update-issue")
    else:
        evidence.append("WARN: canonical jira: update-issue route not explicitly named")

    return _check("atlassian-story-triage-draft-only", status="pass" if ok else "fail",
                  evidence=evidence)


def check_atlassian_team_agent_readiness_separate() -> dict:
    """Team readiness and agent-execution readiness are separate concepts."""
    skill = ROOT / "packs" / "atlassian" / ".apm" / "skills" / "jira-team-status" / "SKILL.md"
    evidence = []
    ok = True

    if not _exists(skill):
        return _check("atlassian-team-agent-readiness-separate", status="fail",
                      evidence=["MISSING: jira-team-status/SKILL.md"])

    text = skill.read_text(encoding="utf-8")
    if "team readiness" in text.lower() and "agent-execution readiness" in text.lower():
        evidence.append("Both 'team readiness' and 'agent-execution readiness' named in SKILL.md")
    else:
        evidence.append("FAIL: Both readiness models must be named in SKILL.md")
        ok = False

    if "explicit" in text.lower() and "optional" in text.lower():
        evidence.append("Agent-execution readiness declared as explicit optional lens")
    else:
        evidence.append("WARN: explicit/optional framing for agent-execution readiness not found")

    return _check("atlassian-team-agent-readiness-separate", status="pass" if ok else "fail",
                  evidence=evidence)


def check_atlassian_activation_evals() -> dict:
    """Atlassian activation evals exist for all three Jira responsibilities."""
    evals_base = ROOT / "packs" / "atlassian" / ".apm" / "skills"
    evidence = []
    ok = True
    required = {
        "jira-team-status": "evals/evals.json",
        "jira-story-triage": "evals/evals.json",
        "jira": "evals/evals.json",
    }
    for skill, rel in required.items():
        path = evals_base / skill / rel
        if _exists(path):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                count = len(data.get("evals", []))
                evidence.append(f"{skill}: {count} evals in {rel}")
            except (json.JSONDecodeError, KeyError):
                evidence.append(f"{skill}: evals.json exists but malformed")
        else:
            evidence.append(f"MISSING: {skill}/{rel}")
            ok = False

    return _check("atlassian-activation-evals", status="pass" if ok else "fail",
                  evidence=evidence)


def check_atlassian_deterministic_tests() -> dict:
    """Deterministic behavior tests for jira-team-status/jira-story-triage pass."""
    test_file = (ROOT / "packs" / "atlassian" / ".apm" / "skills"
                 / "jira-team-status" / "tests" / "test_contract.py")
    evidence = []

    if not _exists(test_file):
        return _check("atlassian-deterministic-tests", status="fail",
                      evidence=["MISSING: jira-team-status/tests/test_contract.py"])

    passed, out = _run_validator([PY, "-m", "pytest", str(test_file), "-q", "--tb=short"])
    lines = out.splitlines()
    # Report last 3 lines (summary)
    summary = "\n".join(lines[-3:]) if len(lines) >= 3 else out
    evidence.append(summary)
    return _check("atlassian-deterministic-tests", status="pass" if passed else "fail",
                  evidence=[summary])


def check_atlassian_readme_accuracy() -> dict:
    """Atlassian README claims agree with executable behavior."""
    readme = ROOT / "packs" / "atlassian" / "README.md"
    evidence = []
    ok = True

    if not _exists(readme):
        return _check("atlassian-readme-accuracy", status="fail",
                      evidence=["MISSING: packs/atlassian/README.md"])

    text = readme.read_text(encoding="utf-8")
    required_claims = [
        ("Starts read-only", "jira-team-status read-only claim"),
        ("Draft only", "jira-story-triage draft-only claim"),
        ("Read-only", "read-only boundary in what-you-can-do section"),
    ]
    for claim, label in required_claims:
        if claim in text:
            evidence.append(f"README contains: '{claim}' ({label})")
        else:
            evidence.append(f"FAIL: README missing claim: '{claim}' ({label})")
            ok = False

    return _check("atlassian-readme-accuracy", status="pass" if ok else "fail",
                  evidence=evidence)


# ── main orchestration ─────────────────────────────────────────────────────────

def _all_checks() -> list[dict]:
    return [
        # Area A: Product Documentation
        check_product_documentation_canonical(),
        check_compatibility_pack_deprecated(),
        check_site_grouping_canonical(),
        check_guide_doctrine(),
        # Area B: Journey framework
        check_journey_sync(),
        check_journey_contract_lint(),
        check_journey_parity(),
        check_journey_subset_allowed(),
        # Area C: Phase 2C UI primitives
        check_phase2c_ui_primitives(),
        # Area D: Atlassian contract
        check_atlassian_version_metadata(),
        check_atlassian_first_value(),
        check_atlassian_team_status_read_only(),
        check_atlassian_story_triage_draft_only(),
        check_atlassian_team_agent_readiness_separate(),
        check_atlassian_activation_evals(),
        check_atlassian_deterministic_tests(),
        check_atlassian_readme_accuracy(),
    ]


def _head_sha() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False, cwd=ROOT,
        )
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except FileNotFoundError:
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 3 readiness gate for the Atlassian retrofit."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    checks = _all_checks()
    failing = [c for c in checks if c["status"] in ("fail", "unverified")]
    ready = len(failing) == 0

    if args.json:
        result = {
            "phase": "atlassian-phase3",
            "ready": ready,
            "head": _head_sha(),
            "checks": checks,
        }
        print(json.dumps(result, indent=2))
    else:
        _ICONS = {"pass": "✓", "fail": "✗", "skipped": "—", "unverified": "?"}
        print(f"\n{'=' * 62}")
        print("  Phase 3 Readiness Report — Atlassian End-to-End Retrofit")
        print(f"{'=' * 62}")
        print(f"  HEAD: {_head_sha()[:12]}\n")
        for c in checks:
            icon = _ICONS.get(c["status"], "?")
            print(f"  {icon}  {c['id']}")
            for ev in c["evidence"]:
                print(f"       {ev}")
        print(f"\n{'=' * 62}")
        if ready:
            print("  READY FOR PHASE 3")
        else:
            print(f"  NOT READY FOR PHASE 3 — {len(failing)} check(s) failing:")
            for c in failing:
                print(f"    ✗  {c['id']}")
        print(f"{'=' * 62}\n")

    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
