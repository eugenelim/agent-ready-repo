# Spec: catalogue-ci-export-boundary

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** `spec/catalogue-ci-contract-guide` (Shipped)
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full (structural/public-interface change — the export-catalogue skill's documented
export surface is a public interface that adopters depend on)

## Objective

The export-catalogue skill must make its CI boundary unambiguous and verifiable.
Today, `guides/_shared/` always travels by step 6, so the CI contract guide is
eligible by construction — but the skill says nothing about it. The strip list says
"release workflows" without naming CI provider directories, leaving open the
possibility that an agent interpreting the skill broadly would copy `.github/workflows/`
or similar CI implementation files to the export target.

After this spec ships:
1. `SKILL.md` and `transform-manifest.md` explicitly state that
   `guides/_shared/reference/catalogue-ci-contract.md` is eligible for export.
2. The strip documentation explicitly excludes CI workflow and pipeline
   implementation using positive allowlist framing — the export surface is bounded
   to `guides/`, projected tools, and seeded scaffold; CI files are outside it.
3. `export_verify.py` gains a `check_ci_boundary()` function that the agent calls
   in step 10 (Verify, fail-closed) to detect CI implementation files in the
   export target.
4. Tests verify: neutral guide eligible, CI implementation excluded (known and
   unknown providers), legitimate `.github/` adapter content passes, policy does
   not rely solely on known provider filenames, white-label behavior fail-closed.

## Boundaries

### Always do

- Use positive allowlist framing in documentation: name what IS in the export
  surface, not only what is excluded.
- Scope `.github/` detection to `.github/workflows/` — Copilot legitimately
  projects to `.github/skills/`, `.github/agents/`, `.github/hooks/`, and
  `.github/instructions/`; these must not be flagged.
- Test both known-provider CI paths (`.github/workflows/`) and structural
  unknown-provider detection; include a negative test for legitimate `.github/`
  adapter content.
- Extend `export_verify.py` — add to it, do not change existing behavior.

### Ask first

- Any change to export procedure steps 1–9 beyond strip/include wording
  clarifications and the verify scope addition.
- Adding a pre-export scrubber that rewrites CI badge URLs inside guide content
  before staging them — that's a different mechanism; raise if the need surfaces.

### Never do

- Implement the full export procedure as Python code — it is agent-executed by
  design; automating it duplicates agent behavior.
- Modify existing `verify()` function logic or the identity-anchor leak check.
- Flag `.github/skills/`, `.github/agents/`, `.github/hooks/`, or
  `.github/instructions/` as CI violations — these are Copilot adapter
  projection paths that are legitimate export content.
- Add CI content to, or remove any guide from, `guides/_shared/` — this spec only
  updates skill documentation and the verify helper.
- Cite RFC, ADR, or spec paths in the shipped skill files (SKILL.md,
  transform-manifest.md, scripts/).
- Scope into `spec/catalogue-ci-documentation` — discovery hooks for adopters
  (guides/README.md, CLI reference, etc.) belong to that spec.

## Testing Strategy

- **AC1–AC5 (documentation):** visual/manual QA. Read the updated SKILL.md and
  transform-manifest.md end-to-end; confirm positive allowlist framing is present
  and CI boundary is explicit with the `.github/workflows/`-specific scope.
- **AC6–AC7 (check_ci_boundary):** TDD. Red stubs first, then implement, then
  confirm tests are green. Run with `pytest scripts/test_export_ci_boundary.py`
  from the skill's `scripts/` directory (matches existing test runner pattern for
  `test_export_verify.py`).
- **AC8 (regression):** Run all existing tests in `scripts/` and confirm no
  regressions: `pytest scripts/test_export_verify.py scripts/test_integration_export.py`.

## Acceptance Criteria

**Documentation — SKILL.md**

- [x] AC1: `SKILL.md` step 3 (Strip) explicitly states that CI workflow and
  pipeline implementation files are excluded from the export surface. Named
  examples scoped precisely: `.github/workflows/` (not the `.github/` root —
  adapter projection paths `.github/skills|agents|hooks|instructions/` are
  legitimate export content), `.gitlab-ci.yml`, `Jenkinsfile`, `.travis.yml`,
  CI-specific trigger config and helper scripts, workflow status badges.
  Uses positive allowlist framing: "The export surface is bounded to guides/,
  projected tools, and seeded scaffold — CI implementation files are outside
  this surface; no credentials are transported."
- [x] AC2: `SKILL.md` step 6 (Stage transportable guides) explicitly states that
  `guides/_shared/reference/catalogue-ci-contract.md` is eligible for export as
  part of `guides/_shared/`, and that the guide is the portable CI contract
  adopters receive — target chooses its own CI system; no CI workflow is generated
  or copied; no credentials are transported; no CI provider is assumed.
- [x] AC3: `SKILL.md` step 10 (Verify, fail-closed) explicitly states that the
  fail-closed check includes `check_ci_boundary()` — no CI implementation files in
  the export target — in addition to the existing upstream-identity anchor check.

**Documentation — transform-manifest.md**

- [x] AC4: `transform-manifest.md` section 1 (STRIP) is updated to explicitly list
  CI workflow/pipeline exclusions — `.github/workflows/` (not the broader `.github/`
  root), `.gitlab-ci.yml`, `Jenkinsfile`, workflow status badges, CI-specific
  env-var names — and includes the positive allowlist statement: "CI implementation
  files are not part of the export surface; the surface is bounded to guides/,
  projected tools, and seeded scaffold; no credentials are transported."
- [x] AC5: `transform-manifest.md` section 4 (GUIDES) explicitly states that
  `guides/_shared/` always travels and includes `catalogue-ci-contract.md`; adds
  the guidance: the target receives the neutral CI contract and chooses its own CI
  system — no CI workflow is copied, no credentials are transported, and no CI
  provider is assumed.

**Code — export_verify.py**

- [x] AC6: `export_verify.py` gains `check_ci_boundary(target: Path) -> list[Violation]`
  that returns non-empty on a target containing any of:
  - A file under `.github/workflows/` (scoped path prefix — NOT the `.github/`
    root; `.github/skills/`, `.github/agents/`, `.github/hooks/`, and
    `.github/instructions/` are legitimate and must not be flagged)
  - A root-level file named `.gitlab-ci.yml`, `Jenkinsfile`, or `.travis.yml`
    (known provider root files)
  - A file *under* (not at root-level beside) a dot-directory at the target root
    that is not `.claude`, `.agents`, or `.github` — flagged as structural
    unknown-provider detection (`.github` is allowlisted because `.github/workflows/`
    is already caught by Check 1 above, and `.github/skills|agents|hooks|instructions/`
    are legitimate Copilot adapter paths; this satisfies "policy does not rely solely
    on known provider filenames")
  - A file in any location whose content contains a GitHub Actions badge URL
    (pattern: `https?://[^)\s]*github[^)\s]*/[^)\s]+/[^)\s]+/actions/workflows/`,
    which requires owner + repo before `/actions/workflows/` — matching the canonical
    badge URL shape); badge scan covers all text files in the target, not only guide files
  Returns empty list on a target containing only legitimately exported content:
  guide files, docs scaffold, `.claude/skills/`, `.agents/skills/`, root scaffold
  files, and `.github/skills/`, `.github/agents/`, `.github/hooks/`,
  `.github/instructions/`.
  Note on host-specific secret names (e.g. `ARTIFACTORY_TOKEN`,
  `ANTHROPIC_API_KEY`): these are covered transitively — they appear only in CI
  workflow files that the path-based checks already exclude. No separate content
  scan for secret variable names is added; the path exclusion is the sufficient
  boundary.

**Tests — test_export_ci_boundary.py**

- [x] AC7: `scripts/test_export_ci_boundary.py` (new) contains and all pass:
  - `test_ci_contract_guide_eligible`: a target with only
    `guides/_shared/reference/catalogue-ci-contract.md` passes `check_ci_boundary`
    (returns `[]`).
  - `test_github_workflow_flagged`: a target with
    `.github/workflows/publish-catalogue.yml` fails `check_ci_boundary` with a
    violation.
  - `test_github_adapter_path_passes`: a target with
    `.github/skills/core/SKILL.md` (a legitimate Copilot adapter projection)
    passes `check_ci_boundary` (returns `[]`). This test guards against false
    positives on the `.github/` root.
  - `test_ci_root_file_flagged`: a target with a root `Jenkinsfile` fails
    `check_ci_boundary` with a `ci_path` violation (exercises Check 2, the
    known root-level CI file path; guards against Check 2 being deleted while
    all other tests remain green).
  - `test_unknown_provider_flagged`: a target with `.ci/step.yml` (a fictional
    provider's dot-directory — not in `.claude` or `.agents`) fails
    `check_ci_boundary` via the dot-directory structural check (satisfies "policy
    does not rely solely on known provider filenames").
  - `test_badge_url_in_guide_flagged`: a target with
    `guides/core/README.md` containing a GitHub Actions badge URL fails
    `check_ci_boundary` with anchor `"ci_badge_url"`.
  - `test_badge_url_outside_guides_flagged`: a target with a root `README.md`
    containing a GitHub Actions badge URL also fails `check_ci_boundary`
    (confirms badge scan is not limited to `guides/`).
  - `test_clean_export_passes`: a target with a realistic scaffold (guides,
    docs, `.claude/skills/`, `.agents/skills/`, `.github/skills/`) and no CI
    files passes `check_ci_boundary` (returns `[]`) and the existing `verify()`
    in white-label mode with no anchors.

**Regression**

- [x] AC8: All tests in `scripts/test_export_verify.py` and
  `scripts/test_integration_export.py` still pass unchanged.

## Assumptions

- Technical: `export_verify.py` is the right extension point — step 10 of the
  export procedure already calls this script; extending it keeps the verify step
  unified.
- Technical: `Violation` in `export_verify.py` is a usable type for CI boundary
  findings; reusing it avoids introducing a new type.
- Technical: The `_skip_by_ext` helper in `export_verify.py` covers binary files;
  `check_ci_boundary` reuses it for all file reads.
- Technical: Copilot projects to `.github/skills/`, `.github/agents/`,
  `.github/hooks/`, `.github/instructions/` — these must not be flagged
  (confirmed from `packages/agentbundle/agentbundle/_data/adapter.toml`).
- Product: No current `guides/_shared/` files contain GitHub Actions badge URLs
  (confirmed during spec authoring: adapter-support.md has `.github/instructions/`
  adapter-path references, not CI badge URLs).
- Product: Host-specific secret variable names (e.g. `ARTIFACTORY_TOKEN`) appear
  only inside CI workflow files; path exclusion of those files is the sufficient
  boundary without a separate content scan.
- Product: The export procedure is agent-executed (not automated Python) — the
  `check_ci_boundary` function is a verify-step helper the agent calls, not a
  replacement for the procedure's strip logic.
- Process: `spec/catalogue-ci-documentation` owns the adopter-discovery surfaces
  (guides/README.md, CLI reference, etc.); this spec does not touch them.
