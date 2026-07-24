# Spec: agentbundle-enterprise-distribution-release

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0072 (full initiative RFC; this spec closes the release step),
  spec/packstate-source-provenance, spec/https-catalogue-channels,
  spec/source-conflict-install-guard, spec/list-installed-update-status,
  spec/upgrade-bulk-all, spec/organization-artifactory-bootstrap,
  spec/package-catalogue-command, spec/artifactory-publishing-workflow,
  spec/corporate-update-documentation
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The AgentBundle Enterprise Distribution initiative (ini-004) delivers nine features
across M1–M6 in separate PRs. Without a coordinated release step, those features are
invisible to adopters running `pip install agentbundle` — the PyPI listing stays at
0.12.1, the CHANGELOG has no entry for the new capabilities, and the README describes
none of them.

This spec coordinates the release: bump the version to 0.13.0 (semver minor — three
new CLI surfaces: `--format`, `--all`, `package-catalogue`), update the CHANGELOG and
PyPI README to reflect the new enterprise distribution capabilities, push the tag
`agentbundle-v0.13.0`, and trigger the existing release workflow.

Done means `agentbundle --version` reports `0.13.0`, the PyPI package page describes
enterprise distribution, and the tag points to a commit on main whose tree contains
all M1–M6 implementation artifacts (CLI surfaces, source code, and guide deliverables).
No new code is introduced; this spec coordinates the publication of changes already
implemented upstream.

## Boundaries

### Always do

- Bump both `packages/agentbundle/pyproject.toml` (`version`) and
  `packages/agentbundle/agentbundle/version.py` (`CLI_VERSION`) to `"0.13.0"` in the
  same PR — the release workflow (`release-agentbundle.yml`) asserts that the tag,
  pyproject version, and CLI_VERSION are all equal.
- Verify all nine M1–M6 implementing specs have their code merged to main — confirmed
  via the artifact-layer checks in AC13(b), not workspace.toml metadata alone — before
  pushing the release tag. (Note: `workspace.toml ["ini-004".work].shipped` entries
  signal "spec + plan authored; adversarial review Clean," not "implementation merged."
  The artifact layer is the authoritative code-presence gate.)
- Use only `example.test` or subdomains as hostnames in all README examples and
  CHANGELOG copy — RFC-0072 security constraint applies here as it does to every
  ini-004 spec.
- Ensure no credentials, API tokens, bearer tokens, or real org names appear in any
  documentation added or updated by this spec.
- Push the tag only after the PR merges to main and `build-and-smoke` passes.

### Ask first

- Any target version other than `0.13.0` — if the semver analysis changes (e.g.,
  because an M1–M6 PR introduces a breaking change requiring a major bump or contains
  only patches), confirm the new version before bumping.
- Amending the release workflow (`.github/workflows/release-agentbundle.yml`) — this
  spec uses the workflow as-is; changes to it are out of scope and need their own spec.

### Never do

- Push the release tag before all M1–M6 PRs are merged to main.
- Add a runtime dependency to `packages/agentbundle/pyproject.toml` — `dependencies`
  must remain `[]`; the Python 3.11 stdlib-only constraint from RFC-0031 and RFC-0072
  is unconditional.
- Publish from a branch other than main (enforced mechanically by the workflow's
  `git merge-base --is-ancestor` assertion, and stated here as a hard rule).
- Include real org names, real Artifactory URLs, or real credentials anywhere in the
  delivered documentation.
- Skip the `build-and-smoke` CI gate before triggering the publish job.

## Testing Strategy

Two modes apply:

**Goal-based check** — for the mechanical changes: version fields in both files
(grep-verifiable), CHANGELOG structure (first version heading is `[0.13.0]`),
README section presence (`grep -F "## Enterprise distribution"`), and
`build-and-smoke` CI gate green on the PR. These are configuration and documentation
changes; there is no behavioral logic to test.

**Visual / manual QA** — for the end-to-end publish: push the tag, watch the
`release-agentbundle` workflow run, install from PyPI in a fresh venv, verify
`agentbundle --version` reports `0.13.0`, and confirm the PyPI package page shows the
updated long description. One manual pass. The OIDC handshake between GitHub Actions
and PyPI is not unit-testable from within this repo.

TDD does not apply — no new behavioral logic is introduced.

## Acceptance Criteria

**Version bump.**

- [ ] AC1. `packages/agentbundle/pyproject.toml` declares `version = "0.13.0"`.
  Verifier: `grep 'version = "0.13.0"' packages/agentbundle/pyproject.toml` exits 0.
- [ ] AC2. `packages/agentbundle/agentbundle/version.py` declares
  `CLI_VERSION = "0.13.0"`. Verifier: `grep 'CLI_VERSION = "0.13.0"' packages/agentbundle/agentbundle/version.py` exits 0.
- [ ] AC3. After building and installing the wheel into a fresh venv, `agentbundle --version` reports `0.13.0`.

**CHANGELOG.**

- [ ] AC4. `packages/agentbundle/CHANGELOG.md` has `## [0.13.0]` as the first version
  heading (directly after the file's prose header). Verifier:
  `grep -m1 '^## \[' packages/agentbundle/CHANGELOG.md` outputs a line beginning with
  `## [0.13.0] —`.
- [ ] AC5. The `## [0.13.0]` entry's `### Added` section covers all seven M1–M6
  feature clusters, each as a distinct bullet: (a) PackState source provenance — every
  installed row records the actual catalogue source used at install time; the
  historical hard-coded literal is removed; (b) source conflict install guard — same
  pack name, same scope, different source is refused before any file or state is
  written; `--force` does not bypass; (c) `list-installed --format table|json` — JSON
  output for CI pipelines, with status values `up-to-date` / `upgrade-available` /
  `ahead` / `unknown`, machine-readable reason codes for `unknown` rows, `--updates-only`
  filter, and a stable JSON contract (schema_version 1); (d) `upgrade --all
  --scope repo|user` — scoped bulk upgrade with adapter-row granularity, preflight
  before all writes, stop-on-first-failure, outcome tracking, and a stable JSON
  contract; (e) `catalogue+https://` and `archive+https://` source schemes — HTTPS
  catalogue channels with SHA-256 verification and bearer token auth via
  `AGENTBUNDLE_HTTP_BEARER_TOKEN`; (f) organization Artifactory bootstrap — optional
  `[organization.artifactory]` block in the bundled `install-defaults.toml`, five-layer
  source precedence, fail-closed on malformed `enabled = true`; (g) `agentbundle
  package-catalogue` — new command producing a deterministic Artifactory artifact
  layout (versioned archive + channel descriptor JSON) from a catalogue directory.
- [ ] AC6. The `## [0.13.0]` entry includes a section (e.g., `### Documentation`)
  acknowledging the M5b Artifactory publishing workflow guide and the M6 enterprise
  adoption guides (`use-an-artifactory-catalogue.md` and the targeted updates to
  existing guides).
- [ ] AC7. No real hostnames, org names, Artifactory URLs, or credentials appear
  anywhere in the `## [0.13.0]` entry.

**PyPI README.**

- [ ] AC8. `packages/agentbundle/README.md` contains an `## Enterprise distribution`
  section. Verifier: `grep -F "## Enterprise distribution" packages/agentbundle/README.md`
  exits 0.
- [ ] AC9. The enterprise distribution section documents all five capabilities with
  working CLI examples using `example.test` hostnames: (a) HTTPS channel install —
  `agentbundle config set source catalogue+https://artifactory.example.test/agentbundle/catalogues/core/channels/stable.json`
  followed by `agentbundle install --pack core`, with a prose note that the bearer
  token is passed via `AGENTBUNDLE_HTTP_BEARER_TOKEN` and is never stored or printed;
  (b) JSON output for CI — `agentbundle list-installed --format json` and
  `agentbundle list-installed --format json --updates-only`, noting the stable JSON
  contract (schema_version 1); (c) bulk upgrade — `agentbundle upgrade --all --scope
  repo --yes` and `agentbundle upgrade --all --scope user --format json --yes`, noting
  honest partial-failure reporting and the preflight-before-write guarantee; (d)
  catalogue packaging — `agentbundle package-catalogue --root /path/to/catalogue
  --bundle my-packs --release 1.0.0 --channel stable --output dist/`, noting
  determinism (identical inputs produce byte-identical archives); (e) org bootstrap —
  a prose description of the `[organization.artifactory]` block in the bundled
  `agentbundle/_data/install-defaults.toml`, stating that the block ships disabled
  (`enabled = false`) by default and that an org fork with `enabled = true` routes
  developers to the configured channel without a manual `config set source` step.
- [ ] AC10. All hostnames and Artifactory URLs in the enterprise distribution section
  of the README use `example.test` or subdomains only. Verifier: the section contains
  no domains outside `example.test`.
- [ ] AC11. The enterprise distribution section cross-references the enterprise
  adoption guide at exactly `docs/guides/_shared/how-to/use-an-artifactory-catalogue.md`
  (the M6 deliverable). Verifier: `grep -F "use-an-artifactory-catalogue.md"
  packages/agentbundle/README.md` exits 0.
- [ ] AC12. `python -m build && twine check --strict dist/*` exits 0 (strict mode
  treats warnings as failures), confirming the updated README renders without PyPI
  long-description warnings. This check is a mandatory local pre-tag gate run in T4
  — the release workflow uses non-strict `twine check` and cannot substitute for it;
  skipping this local check is a release-blocking omission.

**Release gate (human-verified before tag push).**

- [ ] AC13. All nine M1–M6 code implementations are present on the main branch before
  `agentbundle-v0.13.0` is pushed. The workspace.toml `shipped` list is a cross-check
  on spec completion, not on code merge; the authoritative gate is the artifact layer.
  (a) Workspace cross-check — all nine spec paths appear under `["ini-004".work].shipped`
  in `workspace.toml` (signals specs are doc-complete): spec/packstate-source-provenance,
  spec/https-catalogue-channels, spec/source-conflict-install-guard,
  spec/list-installed-update-status, spec/upgrade-bulk-all,
  spec/organization-artifactory-bootstrap, spec/package-catalogue-command,
  spec/artifactory-publishing-workflow, spec/corporate-update-documentation.
  (b) Artifact layer — all of the following checks pass on the merged main tree:
  — M1a: `! grep -q 'source.*=.*"agent-ready-repo"' packages/agentbundle/agentbundle/config.py`
    exits 0 (hard-coded PackState default removed; `canonicalize_source` retains
    the backward-compat mapping as an explicit rule, which is correct and expected);
  — M1b: `grep -rF "source_conflict" packages/agentbundle/agentbundle/` exits 0
    (source-conflict guard present);
  — M2: `agentbundle list-installed --help | grep -F -- "--format"` exits 0;
  — M3: `agentbundle upgrade --help | grep -F -- "--all"` exits 0;
  — M4a: `grep -rF "catalogue+https" packages/agentbundle/agentbundle/` exits 0;
  — M4a-auth: `grep -rF "AGENTBUNDLE_HTTP_BEARER_TOKEN" packages/agentbundle/agentbundle/` exits 0;
  — M4b: `grep -rF "organization.artifactory" packages/agentbundle/agentbundle/` exits 0;
  — M5a: `agentbundle package-catalogue --help` exits 0;
  — M5b: `test -f docs/guides/_shared/how-to/publish-to-artifactory.md` passes;
  — M6: `test -f docs/guides/_shared/how-to/use-an-artifactory-catalogue.md` passes.

**Tag and publish (visual / manual QA).**

- [ ] AC14. Tag `agentbundle-v0.13.0` exists and points to a commit on main.
  Verifier: `git log --oneline agentbundle-v0.13.0 | head -1` outputs the expected
  merge commit SHA.
- [ ] AC15. The `release-agentbundle` workflow's `build-and-smoke` job completes
  successfully for the tag push: the tag-vs-pyproject assertion passes, the
  tag-vs-CLI_VERSION assertion passes, the tag-on-main ancestry assertion passes,
  the wheel and sdist build, `twine check` passes, the wheel installs into a clean
  venv, and `agentbundle --help` exits 0 on PATH.
- [ ] AC16. The `publish-pypi` job completes successfully. From a clean venv on a
  separate machine: `pip install agentbundle==0.13.0` resolves and installs, and
  `agentbundle --version` reports `0.13.0`.
- [ ] AC17. The PyPI package page for agentbundle version 0.13.0 shows the updated
  long description including the enterprise distribution section.

## Assumptions

- Technical: The release workflow (`.github/workflows/release-agentbundle.yml`)
  requires no changes to support this release — it already asserts tag-vs-pyproject,
  CLI_VERSION parity, tag-on-main ancestry, builds wheel and sdist, runs twine check,
  and publishes via Trusted Publisher OIDC. (Source: workflow file read 2026-07-24.)
- Technical: `0.12.1` is the current released version; `0.13.0` is the correct semver
  minor bump given the three new CLI surfaces (`--format`, `--all`, `package-catalogue`).
  (Source: `pyproject.toml` read 2026-07-24; RFC-0072 §Change if accepted.)
- Technical: PyPI Trusted Publisher OIDC is configured for the
  `eugenelim/agent-ready-repo` project under the `pypi` environment — no API token
  rotation is needed. (Source: existing workflow configuration and prior publish history
  visible in CHANGELOG 0.10.0 through 0.12.1.)
- Process: All nine M1–M6 specs are Approved or Shipped at the time this spec is
  authored; they are in `workspace.toml ["ini-004".work].shipped` or will be before the
  tag is pushed. (Source: workspace.toml ini-004 work.shipped list, 2026-07-24.)
- Product: The PyPI README should be updated in the same release PR as the version
  bump, not in a follow-on PR — PyPI shows the README from the published wheel, so
  the updated description should reach PyPI on the first 0.13.0 publish. (Source: task
  specification 2026-07-24; memory note on updating PyPI README on package change.)
