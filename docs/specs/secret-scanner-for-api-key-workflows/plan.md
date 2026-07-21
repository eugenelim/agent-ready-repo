# Plan: secret-scanner-for-api-key-workflows

## Assumption trio

- **Files touched:** `.github/workflows/ci-security.yml` (new),
  `.github/workflows/pack-evals.yml` (edit), `tools/requirements-evals-locked.txt` (new),
  `tools/test-ci-security-workflow.py` (new); possibly inline
  `# actionlint:ignore` or `zizmor.yml` suppressions for pre-existing issues.
- **Tests that demonstrate done:** `python tools/test-pack-evals-workflow.py` exits 0;
  `python tools/test-ci-security-workflow.py` exits 0;
  `actionlint -color` exits 0 on all workflows;
  `zizmor --min-severity high .github/workflows/` exits 0.
- **Not changing:** existing workflow logic (build-check, codeql, docs, pack-evals
  logic), SAST setup, Makefile, any package code. Only CI infrastructure files and
  new tooling are in scope.

## Declined patterns

- Dependabot config — separate backlog item (`ast07-sca-scanner-agentbundle`).
- SHA-pinning all existing workflows' GitHub Actions — large unrelated diff; the
  repo's `@vN` tag-pinning pattern is accepted posture; `unpinned-uses` (HIGH in
  zizmor 1.27.0) is suppressed via `.github/zizmor.yml`, not via severity threshold.
- trufflehog in addition to gitleaks — one scanner is enough for a first gate.
- GPG/cosign signature verification on gitleaks/actionlint binaries — checksum
  verification against publisher's `checksums.txt` is the pragmatic floor; cosign
  is the gold standard and a natural follow-on.
- npm lockfile integrity for `pack-evals.yml` — requires a separate RFC; documented
  as accepted risk in spec Objective.

## Self-coverage disposition record

| Item | Disposition |
|------|-------------|
| gitleaks binary version | Resolved: fetch via API during T1; pin exact version in workflow |
| actionlint binary version | Resolved: pin 1.7.7 (from Assumption 3 in original spec) |
| PyYAML exact version + hash | Resolved: fetch from PyPI JSON API during T2 |
| zizmor severity for unpinned-uses | Resolved: HIGH (not medium as assumed) — suppressed via `.github/zizmor.yml` config listing all existing workflows |
| Pre-existing actionlint errors | Surfaced (value origination): run locally in T4; fix or suppress |
| Pre-existing zizmor high+ findings | Surfaced (value origination): run locally in T5; fix or suppress |
| npm supply-chain risk | Surfaced (irreducible risk — requires separate RFC): documented in spec |
| checksum verification approach | Resolved: verify tarball hash against publisher checksums.txt before extraction |

## Tasks

### T1 — Resolve pinned tool versions

Mode: goal-based check  
Depends on: none

1. Fetch latest stable gitleaks version from GitHub releases API:
   `curl -s https://api.github.com/repos/gitleaks/gitleaks/releases/latest | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])"`
2. Confirm actionlint version 1.7.7 is available; fetch its linux-amd64 checksums.txt URL.
3. Determine zizmor version to pin: `pip install zizmor` then `pip show zizmor | grep Version`.
4. Fetch PyYAML hashes from PyPI:
   `curl -s https://pypi.org/pypi/PyYAML/json | python3 -c "..."`
   — extract version, sdist sha256, cp311 manylinux wheel sha256.

Done when: four version strings and two PyYAML hashes (sdist + cp311 manylinux wheel) confirmed.

### T2 — Create tools/requirements-evals-locked.txt and update pack-evals.yml

Mode: goal-based check  
Depends on: T1

1. Create `tools/requirements-evals-locked.txt` with pinned PyYAML:
   ```
   # Hash-pinned for pack-evals.yml (the repo's first managed-secret workflow).
   # Regenerate: pip-compile --generate-hashes tools/requirements.txt
   PyYAML==<version> \
       --hash=sha256:<sdist-hash> \
       --hash=sha256:<cp311-manylinux-wheel-hash>
   ```
2. In `.github/workflows/pack-evals.yml`, replace:
   `pip install -r tools/requirements.txt`
   with:
   `pip install --require-hashes -r tools/requirements-evals-locked.txt`

Done when: `pip install --require-hashes -r tools/requirements-evals-locked.txt` exits 0.

### T3 — Create tools/test-ci-security-workflow.py

Mode: goal-based check  
Depends on: none (write test before file exists — TDD red-first)

Write `tools/test-ci-security-workflow.py` asserting the security-load-bearing posture
of `ci-security.yml` (mirrors `tools/test-pack-evals-workflow.py` pattern):

- Triggers: `pull_request` and `push` present; `pull_request_target` absent.
- Permissions: top-level `{contents: read}`; no job-level broader permissions.
- gitleaks checkout: `fetch-depth: 0` in the secret-scan job's checkout step.
- gitleaks shell body: no `${{ }}` interpolation (env-var pattern).
- gitleaks step: `--redact` flag present in run body.
- Binary installs: `sha256sum` (or equivalent) appears in each binary-install step
  before the `tar xz` extraction command.
- Concurrency: `cancel-in-progress` expression contains `github.event_name == 'pull_request'`.

Done when: test written and script exits non-zero cleanly (file not found) against
the absent `ci-security.yml` — confirmed green in T7 once T4 creates the file.

### T4 — Create .github/workflows/ci-security.yml

Mode: goal-based check  
Depends on: T1

Create `.github/workflows/ci-security.yml` with:

```
on: pull_request (main) + push (main)
permissions: contents: read
concurrency: cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  secret-scan:
    steps:
      - checkout (fetch-depth: 0)
      - install gitleaks: download tarball + checksums.txt, verify hash, extract
      - run gitleaks detect via env-var pattern (BASE_SHA, EVENT_NAME), --redact

  workflow-security:
    steps:
      - checkout
      - install actionlint: download tarball + checksums.txt, verify hash, extract
      - install zizmor: pip install 'zizmor==<pinned>'
      - run actionlint -color
      - run zizmor --min-severity high .github/workflows/
```

Done when: `actionlint -color .github/workflows/ci-security.yml` exits 0.

Depends on: T1

### T5 — Triage pre-existing actionlint + zizmor findings

Mode: goal-based check  
Depends on: T4

1. Run `actionlint -color .github/workflows/*.yml` on all workflows.
   - For each error: fix inline (if mechanical, e.g., quoting) or add
     `# actionlint:ignore <rule>` with a one-line justification.
2. Run `zizmor --min-severity high .github/workflows/`.
   - Verify `unpinned-uses` does NOT appear (should be medium, below threshold).
   - For any high+ finding: fix or add suppression to `.github/zizmor.yml`.

Done when: both commands exit 0 on all workflows.

### T6 — Initial gitleaks history scan

Mode: goal-based check  
Depends on: T1

1. Install gitleaks locally using the version and checksum from T1:
   ```
   VERSION=<from T1>
   curl -sfL "https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}/gitleaks_${VERSION}_linux_x64.tar.gz" -o gl.tar.gz
   curl -sfL "https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}/checksums.txt" -o gl-checksums.txt
   grep "gitleaks_${VERSION}_linux_x64.tar.gz" gl-checksums.txt | sha256sum -c
   tar xzf gl.tar.gz -C /tmp gitleaks
   ```
   (macOS: use `darwin_arm64` tarball and `shasum -a 256 -c`.)
2. Run `/tmp/gitleaks detect --source . --verbose --redact` on the full repo history.
3. If findings: investigate each; if legitimately historical/rotated, add to `.gitleaksignore`.
4. If `.gitleaksignore` is created, document why in a header comment.

Done when: `/tmp/gitleaks detect --source . --redact` exits 0 (clean or with `.gitleaksignore`).

### T7 — Verify all gates

Mode: goal-based check  
Depends on: T2, T3, T4, T5, T6

1. `python tools/test-pack-evals-workflow.py` exits 0.
2. `python tools/test-ci-security-workflow.py` exits 0.
3. `actionlint -color` exits 0 on all workflows.
4. `pip install --require-hashes -r tools/requirements-evals-locked.txt` exits 0.

Done when: all four commands exit 0.
