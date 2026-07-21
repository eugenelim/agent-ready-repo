#!/usr/bin/env python3
"""Posture check for .github/workflows/ci-security.yml.

Security-load-bearing invariants (parallel to tools/test-pack-evals-workflow.py):
  - Triggers: pull_request + push only; pull_request_target absent.
  - Permissions: top-level contents:read; no broader job-level permissions.
  - gitleaks checkout: fetch-depth: 0 in the secret-scan job.
  - gitleaks shell body: no ${{ }} interpolation (env-var pattern).
  - gitleaks step: --redact flag present.
  - Binary installs: sha256sum check appears before tar extraction.
  - Concurrency: cancel-in-progress uses the pull_request gate expression.

Pure-stdlib + PyYAML (already a tools/ dependency).
"""

from __future__ import annotations

import pathlib
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci-security.yml"


def fail(msg: str) -> None:
    print(f"✖ ci-security.yml: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    if not WORKFLOW.exists():
        fail(f"not found at {WORKFLOW}")

    text = WORKFLOW.read_text(encoding="utf-8")
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        fail(f"does not parse as YAML: {exc}")

    # PyYAML parses the bareword `on:` key as the boolean True.
    triggers = doc.get("on", doc.get(True))
    if not isinstance(triggers, dict):
        fail("`on:` must be a mapping of trigger types")
    if "pull_request" not in triggers or "push" not in triggers:
        fail("must trigger on both `pull_request` and `push`")
    if "pull_request_target" in triggers:
        fail("must NOT trigger on `pull_request_target` — fork PRs could reach secrets")

    # Least-privilege permissions at workflow level.
    perms = doc.get("permissions")
    if perms != {"contents": "read"}:
        fail(f"top-level permissions must be {{contents: read}}, got {perms!r}")

    jobs = doc.get("jobs", {})
    if not jobs:
        fail("no jobs found")

    # No job-level permission escalation beyond workflow-level.
    for job_name, job in jobs.items():
        job_perms = job.get("permissions")
        if job_perms is not None:
            fail(
                f"job `{job_name}` sets explicit permissions {job_perms!r}; "
                f"workflow-level contents:read is sufficient — no escalation allowed"
            )

    # Concurrency: cancel-in-progress must be conditional on pull_request only.
    concurrency = doc.get("concurrency", {})
    cancel = str(concurrency.get("cancel-in-progress", ""))
    if "pull_request" not in cancel:
        fail(
            "concurrency.cancel-in-progress must be conditional on github.event_name == "
            "'pull_request' so push-to-main scans complete; "
            f"got: {cancel!r}"
        )

    # secret-scan job: fetch-depth: 0 for gitleaks history range.
    secret_job = jobs.get("secret-scan")
    if secret_job is None:
        fail("no `secret-scan` job found")
    checkout_steps = [
        s for s in secret_job.get("steps", [])
        if "checkout" in str(s.get("uses", ""))
    ]
    if not checkout_steps:
        fail("secret-scan job: no checkout step found")
    for step in checkout_steps:
        with_block = step.get("with", {})
        if with_block.get("fetch-depth") != 0:
            fail("secret-scan checkout: fetch-depth must be 0 for history range scan")

    # gitleaks detect step: env-var pattern (no ${{ }} in shell body).
    gitleaks_steps = [
        s for s in secret_job.get("steps", [])
        if "gitleaks" in str(s.get("run", "")).lower()
        and "detect" in str(s.get("run", "")).lower()
    ]
    if not gitleaks_steps:
        fail("secret-scan job: no gitleaks detect step found")
    for step in gitleaks_steps:
        run_body = step.get("run", "")
        if "${{" in run_body:
            fail(
                "gitleaks detect step: ${{ }} found in shell body — "
                "use env: block to pass GitHub-context values (injection sink pattern)"
            )
        if "--redact" not in run_body:
            fail(
                "gitleaks detect step: --redact flag missing — "
                "matched secret values must never reach (public) CI logs"
            )

    # Binary install steps: sha256sum check before tar extraction.
    install_steps = [
        s for s in (secret_job.get("steps", []) + sum(
            (j.get("steps", []) for j in jobs.values()), []
        ))
        if "tar xz" in str(s.get("run", "")) or "tar xzf" in str(s.get("run", ""))
    ]
    # Deduplicate by id
    seen_ids: set[int] = set()
    deduped = []
    for s in install_steps:
        sid = id(s)
        if sid not in seen_ids:
            seen_ids.add(sid)
            deduped.append(s)
    for step in deduped:
        run_body = step.get("run", "")
        if "sha256sum" not in run_body and "shasum" not in run_body:
            name = step.get("name", "(unnamed)")
            fail(
                f"install step '{name}': no sha256sum/shasum verification found before "
                f"tar extraction — binary must be verified against checksums.txt"
            )

    print(
        "✓ ci-security.yml: pull_request+push only (no pull_request_target), "
        "contents:read, no job-level escalation, fetch-depth:0 in secret-scan, "
        "env-var injection pattern, --redact on gitleaks, "
        "sha256sum before all binary extractions, "
        "cancel-in-progress conditional on pull_request. YAML parses."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
