# Secret Scanner for API-Key Workflows

- **Status:** Shipped
- **Backlog slug:** `secret-scanner-for-api-key-workflows`
- **Constrained by:** CI-only tooling additions — no ADR required; three new CI dependencies
  (gitleaks, actionlint, zizmor) are recorded here as the authoritative registry entry per
  AGENTS.md § Check before acting.
- **Created:** 2026-07-20
- **Mode:** full (security boundary + new dependency)

## Objective

Wire a secret scanner (gitleaks), a workflow linter (actionlint), and a workflow security
analyzer (zizmor) into CI as a new `ci-security.yml` workflow. Pin the external pip dependency
in `pack-evals.yml` (the repo's first managed-secret workflow) with SHA-256 hashes.

The npm install in `pack-evals.yml` (`@anthropic-ai/claude-code@2.1.185`) is version-pinned
but not hash-verified; it is the larger supply-chain surface next to ANTHROPIC_API_KEY. This
spec narrows its PyYAML-pinning AC to honest scope: it pins the one direct external pip dep
and documents the npm vector as a known accepted risk (npm has no practical per-package hash
verification in `install -g` mode without a lockfile; it requires a separate hardening RFC).

## Acceptance Criteria

- [x] AC1. A new `.github/workflows/ci-security.yml` runs on `pull_request`
        (targeting `main`) and `push` to `main`.
- [x] AC2. `ci-security.yml` declares `permissions: contents: read` at workflow
        level (least-privilege default) with no job-level permission escalation.
- [x] AC3. A `secret-scan` job in `ci-security.yml` installs gitleaks using a
        version-pinned binary download; the SHA-256 is hardcoded in the workflow
        (repo-committed, not fetched from the same origin) so upstream re-tagging
        fails the gate. The job uses `fetch-depth: 0` on checkout. On
        `pull_request` it scans `${BASE_SHA}..HEAD` commits; on `push` it scans
        `${BEFORE_SHA}..HEAD` (incremental range); full-history fallback only when
        the SHA is the zero SHA (new branch push) or absent. All GitHub-context
        values are passed via env vars — not interpolated directly into the shell
        body. `--redact` is passed so matched values are never echoed to (public)
        CI logs. `set -euo pipefail` guards each install step. Exit code 1 fails
        the job when secrets are detected.
- [x] AC4. A `workflow-security` job in `ci-security.yml` installs actionlint
        using a version-pinned binary download; the SHA-256 is hardcoded in the
        workflow (same repo-committed pattern as AC3). actionlint exits 0 on all
        `.github/workflows/*.yml` files.
- [x] AC5. The `workflow-security` job also installs zizmor (via pip, exact version
        pin). `zizmor --min-severity high .github/workflows/` runs and exits 0;
        severity `high`+ findings fail the job. `unpinned-uses` (HIGH in zizmor
        1.27.0) is suppressed via a `.github/zizmor.yml` config file — the repo
        accepts `@vN` tag-pinning as current posture (SHA pinning is backlog). All
        remaining `high`+ findings — including any in pre-existing workflows — are
        addressed in AC11.
- [x] AC6. All GitHub Actions used in `ci-security.yml` follow the repo's existing
        `@vN` tag-pinning pattern with a `# vN.x.y` version comment for auditability.
- [x] AC7. `pack-evals.yml`'s `pip install -r tools/requirements.txt` step is
        replaced by `pip install --require-hashes -r tools/requirements-evals-locked.txt`;
        the new `tools/requirements-evals-locked.txt` pins PyYAML to an exact version
        with SHA-256 hashes for the sdist and the `cp311-manylinux_2_17_x86_64`
        wheel (the specific artifact installed on `ubuntu-latest` / Python 3.11).
- [x] AC8. `tools/test-pack-evals-workflow.py` continues to pass after the
        `pack-evals.yml` edit (posture invariants unchanged).
- [x] AC9. A new `tools/test-ci-security-workflow.py` asserts the security-load-bearing
        posture of `ci-security.yml`: `pull_request`+`push` triggers only (no
        `pull_request_target`), `permissions: contents: read` at workflow level with
        no broader job-level permissions, `fetch-depth: 0` present in the gitleaks
        checkout step, absence of `${{ }}` interpolation in the gitleaks shell body
        (env-var pattern), presence of `--redact` in the gitleaks step, and presence
        of a `sha256sum` or equivalent checksum command before each binary extraction.
- [x] AC10. `actionlint -color` exits 0 on all `.github/workflows/*.yml` files
         including pre-existing ones; any pre-existing error is either fixed inline
         or suppressed with an `# actionlint:ignore <rule>` comment with a one-line
         justification.
- [x] AC11. `zizmor --min-severity high` exits 0 on all `.github/workflows/*.yml`
         files. `unpinned-uses` (ALL 44 pre-existing findings) is suppressed via
         `.github/zizmor.yml` with a justification comment (accepted tag-pinning
         posture). No other high+ findings exist in the current workflow set.
- [x] AC12. `ci-security.yml`'s `concurrency` block uses `cancel-in-progress: true`
         for `pull_request` events only; `push`-to-`main` scans run to completion
         (implemented via `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`).

## Boundaries

### Always do

- Pass all GitHub-context values in the shell via env vars, never `${{ }}` interpolation
  in `run:` bodies (injection sink pattern from pack-evals.yml).
- Verify binary checksums before execution (gitleaks, actionlint).
- Use `--redact` on gitleaks so matched values never reach CI logs.
- Keep `permissions: contents: read` at workflow level.

### Ask first

- Making `ci-security.yml` a required status check (requires a repo settings change —
  not a code change; out of scope for this PR but the natural follow-on).
- Pinning the npm global install with a lockfile (requires a separate RFC on npm global
  install integrity; accepted risk documented in Objective above).

### Never do

- Interpolate `${{ github.event.* }}` or any user-controlled value directly into a
  `run:` shell body — always route through env vars.
- Remove `--redact` from the gitleaks step.
- Broaden `ci-security.yml` permissions to write access.
- Change the gitleaks job trigger to `pull_request_target` (would expose secrets to
  fork PRs).
- Add gitleaks to the Makefile `sast` target (keep CI concerns in `.github/`).

## Testing Strategy

Verification mode: goal-based check.

| AC | Verification |
|----|-------------|
| AC1 | `python tools/test-ci-security-workflow.py` asserts triggers |
| AC2 | `python tools/test-ci-security-workflow.py` asserts permissions |
| AC3 | Same — asserts env-var pattern, --redact presence |
| AC4 | `actionlint -color` exits 0 on `ci-security.yml` |
| AC5 | `pip install zizmor==<version>` + `zizmor --min-severity high .github/workflows/` exits 0 |
| AC6 | Code review |
| AC7 | `pip install --require-hashes -r tools/requirements-evals-locked.txt` exits 0 |
| AC8 | `python tools/test-pack-evals-workflow.py` exits 0 |
| AC9 | `python tools/test-ci-security-workflow.py` exits 0 |
| AC10 | `actionlint -color` exits 0 on `.github/workflows/*.yml` |
| AC11 | `zizmor --min-severity high .github/workflows/` exits 0 |
| AC12 | Code review + test-ci-security-workflow.py |

## Assumptions

1. The repo is public — gitleaks binary is usable without a commercial license.
2. PyYAML is pinned to a specific exact version (e.g., 6.0.2) with hashes fetched
   from PyPI JSON API during EXECUTE.
3. zizmor 1.27.0 classifies `unpinned-uses` as HIGH severity (not medium as
   originally assumed). Suppressed via `.github/zizmor.yml` config (not
   `--min-severity` threshold) — all existing workflows listed as accepted posture.
4. The repo has no pre-existing leaked secrets in git history; if any are found
   during T4, they are addressed before the gate goes live.
5. The npm `install -g` supply-chain risk is a known accepted trade-off, recorded as
   backlog item `pack-evals-npm-lockfile-integrity`; the Objective above is the durable
   record.
