# Spec: catalogue-ci-contract-guide

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none
- **Shape:** docs

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full (structural: new shipped guide in `guides/_shared/reference/`; public
interface: documents stable exit-code + JSON contracts that adopters will rely on)

## Objective

Any organization wiring a CI pipeline for an AgentBundle catalogue — whether
they use GitHub Actions, GitLab CI, Jenkins, or Buildkite — has a single
canonical reference: `guides/_shared/reference/catalogue-ci-contract.md`. The
guide defines the six CI lifecycle phases with portable commands, documents the
responsibility boundary among three parties (AgentBundle CLI, Organization CI,
Host Repository), specifies the stable exit-code and JSON-output contracts for
each catalogue command, and makes publication ordering explicit. It is adopted
clean: no internal RFC/ADR citations, no repo-specific paths.

Three discovery hooks ensure adopters can find the guide from the surfaces they
already read: the `_shared` guide index, the agentbundle CLI reference, and the
catalogue-format reference. AGENTS.local.md and packs/AGENTS.md carry link-only
references for agents working in this repo.

Command-contract tests added alongside the guide verify that the documented
exit codes and JSON output shapes match HEAD, so guide drift produces a CI
failure rather than a silent lie.

## Boundaries

### Always do

- Document commands against HEAD behaviour only — verify flags and exit codes
  with `agentbundle catalogue <cmd> --help` and subprocess invocations before writing.
- Keep the guide in the adopter-facing `guides/` tree; the AGENTS.md entries
  must be link-only (no content duplication).
- Maintain the packs/AGENTS.md line count ≤ 150 and AGENTS.local.md ≤ 250.

### Ask first

- Any new `catalogue` subcommand documentation (self-host, sync-defaults, archive
  verify) beyond lint/verify/package — a separate spec owns that surface.
- Promoting `docs/guides/how-to/create-external-catalogue.md` into the adopter
  `guides/` tree — scoped to `spec/catalogue-ci-documentation`.

### Never do

- Document `--format json` for `catalogue package` — it is not supported in HEAD.
- Include CI provider-specific YAML syntax — the contract is provider-neutral.
- Cite RFC, ADR, or spec paths in shipped guide content.
- Duplicate the exit-code table or command signatures in AGENTS.local.md or
  packs/AGENTS.md — those files link to the guide, period.

## Testing Strategy

- **Guide content (AC1–AC10):** visual/manual QA. Read the guide end-to-end and
  verify each documented command flag and exit code against `agentbundle catalogue
  <cmd> --help` output (goal-based check). The full "happy path" verification:
  run `agentbundle catalogue lint --root . --format json` and
  `agentbundle catalogue verify --root . --format json` against the working
  catalogue, confirm JSON parses and `ok` is true, record stdout + exit code in
  the implementing PR's *How to verify* section.
- **Discovery links (AC11–AC15):** goal-based. `grep` confirms the link is present
  in each target file; `wc -l` confirms no file exceeds its cap.
- **Command contract (AC16–AC21):** TDD. Subprocess invocations of the CLI against
  a fixture catalogue (T7 defines its own `working_catalogue_root` fixture — the
  module-level `_REPO_ROOT` in `test_catalogue_tooling_foundation.py` is private and
  not a pytest fixture). Assert JSON parseability, stdout-only JSON (no mixed output),
  exit codes 0/1 on clean/errors, package exit 0 with output layout, and package
  exit 2 on missing required flags.

## Acceptance Criteria

**Guide content**

- [x] AC1: Guide exists at `guides/_shared/reference/catalogue-ci-contract.md`
  with frontmatter `title`, `summary`, `pack: _shared`, `kind: reference`,
  `status: stable`.
- [x] AC2: Guide documents the responsibility boundary for three parties:
  *AgentBundle CLI* (owns lint/verify/package correctness, stable JSON + exit-code
  contracts, never reads secrets or issues network calls); *Organization CI* (owns
  secrets, network credentials, upload mechanics, publication serialization,
  rollback policy, artifact retention); *Host Repository* (owns workflow files,
  trigger config, internal governance).
- [x] AC3: Guide documents all six CI lifecycle phases in order: (1) tool
  acquisition, (2) change validation, (3) release packaging, (4) publication,
  (5) post-publication verification, (6) evidence retention — each with the
  portable command(s) or responsibilities for that phase.
- [x] AC4: Guide documents `agentbundle catalogue lint --root . --format json`:
  stdout is a JSON object with keys `schema_version`, `command`, `operation`,
  `agentbundle_version`, `catalogue_schema_version`, `ok`, `diagnostics`; human
  output goes to stderr; exits 0 if all checks pass, 1 if any error is emitted.
- [x] AC5: Guide documents `agentbundle catalogue verify --root . --format json`
  with the same JSON schema as lint; exits 0 on clean, 1 on any failure.
- [x] AC6: Guide documents `agentbundle catalogue package` with the four required
  flags (`--bundle`, `--release`, `--channel`, `--output`) and the optional flags
  (`--root` defaults to `.`; `--source-revision`; `--minimum-agentbundle-version`;
  `--published-at`) — without `--format json` (not supported). Documents the output
  layout: `<output>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz`,
  `.sha256` sidecar, `channels/<channel>.json` descriptor.
- [x] AC7: Guide documents exit codes: 0 success, 1 validation/operational failure,
  2 CLI usage error. `catalogue package` follows the standard convention: exits 2
  on missing required flags (argparse intercepts before the handler runs).
- [x] AC8: Guide makes publication ordering explicit: write the archive first, the
  SHA256 sidecar second, and the channel descriptor (`channels/<channel>.json`)
  last. The channel descriptor is the live pointer; writing it last minimises the
  window in which the descriptor references a not-yet-present archive.
- [x] AC9: Guide has a secrets / TLS section that clearly states AgentBundle CLI
  commands never read secrets and never issue network calls; TLS verification and
  credential injection are exclusively Organization CI's responsibility.
- [x] AC10: Guide includes a *See also* or *Related* section that cross-references
  `guides/_shared/reference/agentbundle.md` and `guides/_reference/catalogue-format.md`.

**Discovery**

- [x] AC11: `guides/_shared/README.md` Reference section links to the guide.
- [x] AC12: `guides/_shared/reference/agentbundle.md` has a short "Catalogue CI"
  paragraph pointing readers to the CI contract guide.
- [x] AC13: `guides/_reference/catalogue-format.md` Validation section links to the <!-- Moved 2026-08-18 by spec/guide-metadata-completion to `guides/_shared/reference/catalogue-format.md`; the public route is unchanged. -->
  CI contract guide for CI pipeline patterns.

**AGENTS.md references**

- [x] AC14: `AGENTS.local.md` has a one-line cross-reference to the CI contract
  guide; file remains ≤ 250 lines.
- [x] AC15: `packs/AGENTS.md` has a one-line cross-reference to the CI contract
  guide; file remains ≤ 150 lines.

**Command contract tests**

- [x] AC16: `catalogue lint --root <fixture> --format json` stdout `json.loads()`
  without error and the resulting dict contains keys `schema_version`, `command`,
  `ok`, `diagnostics`.
- [x] AC17: `catalogue verify --root <fixture> --format json` stdout `json.loads()`
  without error with the same required keys.
- [x] AC18: With `--format json`, the stdout of lint and verify contains only the
  JSON object — no non-JSON lines mixed in (verified by confirming the raw stdout
  parses cleanly without stripping).
- [x] AC19: `catalogue lint` and `catalogue verify` return exit code 0 on a clean
  catalogue and exit code 1 when the run reports at least one error-severity
  diagnostic.
- [x] AC20: `catalogue package` with all required flags returns exit code 0 on
  success; the output directory contains the expected archive, SHA256 sidecar, and
  channel descriptor at the documented paths.
- [x] AC21: `catalogue package` invoked without required flags exits 2 (argparse
  usage error), confirming the standard 0/1/2 convention applies.

## Assumptions

- Technical: HEAD `catalogue lint` and `catalogue verify` both support `--format json`
  (source: `commands/catalogue_lint.py`, `commands/catalogue_verify.py` — verified
  pre-session).
- Technical: HEAD `catalogue package` does NOT support `--format json` (source:
  `commands/catalogue_package.py` — verified pre-session; guide must not document it).
- Technical: `catalogue package` exits 2 when required flags are absent (argparse
  intercepts before the handler runs — verified against HEAD: `python3 -m agentbundle
  catalogue package` → exit 2). Follows the standard 0/1/2 convention.
- Technical: publication ordering (archive → SHA256 → channel.json) is the correct
  safe upload order because the channel descriptor is the live pointer read by
  consumers; writing it last minimises the window where a descriptor references a
  not-yet-uploaded archive.
- Technical: existing test infrastructure in
  `packages/agentbundle/tests/unit/test_catalogue_tooling_foundation.py` provides
  fixture catalogue helpers that the new contract tests can reuse.
- Product: the target reader of this guide is an organization CI engineer who knows
  basic CI concepts but may not know the AgentBundle toolchain; the guide must be
  self-contained for that reader.
- Process: `spec/catalogue-ci-documentation` (the follow-on spec) handles the
  deeper adopter-facing surfaces: a how-to for setting up catalogue CI, cross-links
  from `guides/catalogue-curation/`, and the PyPI README update. Those are
  out of scope here.
