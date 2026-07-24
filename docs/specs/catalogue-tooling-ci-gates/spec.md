# Spec: Catalogue Tooling — CI Gates

- **Status:** Draft
- **Owner:** eugenelim
- **Initiative:** ini-005 AgentBundle Portable Catalogue Tooling
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ini-005 brief Bucket 13; all prior Wave 1-5 specs
- **Shape:** service

> **Spec contract:** this document defines what "done" means.

## Objective

After all Wave 1-5 specs ship, no required CI job confirms that the portable
engine works against an unrelated external catalogue, that enterprise distribution
defaults are correctly packaged, or that the release impact of changes is
detected. Nine required CI gates from Bucket 13 must be added as named required
jobs.

This spec adds all 9 gates (A-I) as new GitHub Actions jobs, replacing any
ad-hoc or manually invoked pytest files that duplicate them.

## Boundaries

### Always do

- **Gate A — `agentbundle-tests`**: replace any individual pytest file invocations
  with a single job that runs `python -m pytest` from `packages/agentbundle/`,
  discovering BOTH `tests/` and `agentbundle/build/tests/`. Matrix: Ubuntu
  Python 3.11, Ubuntu Python 3.12, Windows Python 3.11.
- **Gate B — `external-catalogue-smoke`**: job that builds the wheel, installs it
  in isolation, creates a minimal external catalogue (no Makefile, no tools/),
  runs `agentbundle catalogue lint/verify/build/package`, verifies the archive,
  extracts and runs `list-packs`. Proves portable engine works outside this repo.
- **Gate C — `enterprise-agentbundle-distribution`**: builds enterprise wheel with
  a temporary `catalogue.toml` containing example.test Artifactory URL; inspects
  wheel + zipapp for `install-defaults.toml`; verifies preferred-adapter and
  Artifactory source behavior; scans artifacts for test bearer token and FAILS
  if found; no external network access.
- **Gate D — `catalogue-artifact-smoke`**: runs against this repository:
  sync-defaults --check, lint, verify, package (×2 for determinism), compare
  bytes, confirm all three required files, verify archive + checksum, extract,
  validate, list-packs, temporary install.
- **Gate E — `catalogue-disconnected-smoke`**: after artifact generation, disable
  or mock outbound networking; transfer only archive + sidecar to clean tmpdir;
  verify → extract → use as local catalogue → list-packs → install; assert no
  HTTP resolver invoked; assert no token required.
- **Gate F — `catalogue-repo-rewire`**: verify Makefile targets call canonical
  engine; old compat entry points delegate correctly; no portable logic only in
  tools/; repo-only gates run after portable verification; moved shims work;
  Flow E examples match actual paths; catalogue.toml + defaults synchronized;
  source and bundled schemas synchronized.
- **Gate G — `agentbundle-release-impact`**: path-sensitive diff check against
  merge base. Triggers on changes to `agentbundle/catalogue_tooling/`, main CLI
  definitions, bundled schemas, JSON contracts, portable recipes, package
  defaults semantics. Does NOT trigger for `catalogue.toml`, `packs/`,
  `profiles/`, `tools/catalogue/`, repo-only docs. Requires approved release
  indicator (changelog fragment, version update, or reviewed no-release
  declaration) when triggered.
- **Gate H — AgentBundle release workflow**: before PyPI publication, require
  A + B + C + D + E + wheel content inspection + existing provenance. Fail if
  install-defaults.toml is stale relative to catalogue.toml.
- **Gate I — Artifactory publication template**: add or update a non-secret
  publication workflow example: verify → package → upload archive → upload
  sidecar → verify uploaded artifact → upload channel descriptor LAST.
  No Artifactory credentials in workflow YAML or AgentBundle.
- All jobs run using example.test values only. No external network to real
  endpoints.
- All existing CI jobs pass.

### Ask first

- Adding macOS matrix leg to Gate A (capacity-dependent).
- Making Gate E use real network namespaces vs dependency injection.
- Splitting Gate H into a separate workflow file vs adding to existing release workflow.

### Never do

- Replace complete `python -m pytest` discovery (Gate A) with a manually maintained
  list of individual test files.
- Embed production Artifactory URLs, credentials, or real bearer tokens in any
  workflow YAML.
- Run model-backed evals, SAST, or changelog enforcement as part of portable
  catalogue verification in any gate.

## Testing Strategy

- **Goal-based** for each gate's existence: each gate's job ID exists in the
  relevant workflow YAML file.
- **Goal-based** for Gate A completeness: run `python -m pytest --collect-only`
  from `packages/agentbundle/`; assert count of collected tests matches a
  previously counted baseline.
- **TDD** for Gate G path sensitivity: a diff touching `agentbundle/catalogue_tooling/`
  triggers release-impact; a diff touching only `packs/` does not.

## Acceptance Criteria

- [ ] AC1: Gate A job `agentbundle-tests` exists with Ubuntu+3.11, Ubuntu+3.12,
  Windows+3.11 matrix. Uses `python -m pytest` from `packages/agentbundle/`.
- [ ] AC2: Gate B job `external-catalogue-smoke` exists. Creates external
  catalogue with no Makefile/tools/. All 5 catalogue commands succeed.
- [ ] AC3: Gate C job `enterprise-agentbundle-distribution` exists. Scans
  artifacts for test bearer token — fails if found. No external network calls.
- [ ] AC4: Gate D job `catalogue-artifact-smoke` exists. Confirms all three
  required files in archive. Byte-for-byte determinism under SOURCE_DATE_EPOCH.
- [ ] AC5: Gate E job `catalogue-disconnected-smoke` exists. No HTTP resolver
  invoked; no token required. Uses network guard or dependency injection.
- [ ] AC6: Gate F job `catalogue-repo-rewire` exists. Confirms Makefile calls
  canonical commands; shims delegate; no portable logic in tools/.
- [ ] AC7: Gate G job `agentbundle-release-impact` exists. Changes to
  `agentbundle/catalogue_tooling/` trigger; changes to `catalogue.toml` alone
  do not.
- [ ] AC8: Gate H is wired into the existing release/publish workflow.
- [ ] AC9: Gate I Artifactory publication template is documented and uses
  example.test values only.
- [ ] AC10: All existing CI jobs pass.

## Assumptions

1. All Wave 1-5 specs ship before this spec. Gate jobs call the new commands
   that Wave 1-5 built.
2. The Artifactory publication template (Gate I) is a documented example, not
   a live CI job that contacts real Artifactory.
3. Network isolation for Gate E uses Python-level mocking or CI network
   restrictions (not OS-level network namespaces which require root).
4. The release-impact check (Gate G) uses a Python script, not an external action,
   to avoid new GitHub Action dependencies.
