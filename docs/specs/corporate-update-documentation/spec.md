# Spec: Corporate Update Documentation

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0072 (follow-on spec deliverable), spec/packstate-source-provenance, spec/https-catalogue-channels, spec/list-installed-update-status, spec/upgrade-bulk-all, spec/source-conflict-install-guard, spec/organization-artifactory-bootstrap, spec/package-catalogue-command, spec/artifactory-publishing-workflow
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Enterprise adopters — platform engineers configuring an internal Artifactory mirror, developers in locked-down corporate networks, and IT teams distributing agent tooling via MDM — can follow documented sequences to: configure agentbundle against an Artifactory-hosted catalogue, run scoped bulk upgrades with machine-readable JSON output for CI automation, understand and remediate source-conflict errors, operate in fully disconnected environments, and review the token-handling, transport, integrity, and runtime security controls. A single primary guide (`use-an-artifactory-catalogue.md`) contains six flows covering every enterprise adoption pattern; four existing shared guides receive targeted updates that weave enterprise context into surfaces where users already land, and the guides index receives a link entry. An adopter reading only the delivered guides completes any of the six flows without undocumented steps.

## Boundaries

### Always do

- Use only `example.test` or subdomains thereof for every hostname, URL, org name, and Artifactory endpoint in every example
- Write all guide content in present-tense, as-built voice
- Cross-reference related guides and specs by relative path (not by RFC or spec number in prose alone)
- Document all six flows (A–F) completely in the primary guide

### Ask first

- Any change to a CLI behavior description that goes beyond what is defined in the upstream ini-004 specs — any apparent discrepancy surfaces before writing
- Any guide restructuring (rename, move, merge) not listed in the deliverables below
- Any example TOML showing `enabled = true` without all four required fields (`base-url`, `repository`, `bundle`, `channel`) present — there is no valid partial-enabled config

### Never do

- Include real hostnames, real org names, real Artifactory instance URLs, real bearer token values, or any placeholder that looks like a real credential
- Include `enabled = true` in any `[organization.artifactory]` example without all four required fields (`base-url`, `repository`, `bundle`, `channel`)
- Describe or imply a TLS-disable option, certificate-ignore flag, or any way to bypass TLS verification
- Describe `--force` as a bypass for source-conflict refusal — it is not
- Show bearer token values in any state output snippet, error message, exception repr, or inline comment
- Modify any Python source file — this is a docs-only spec; no code changes permitted
- Add runtime dependencies

## Testing Strategy

This spec is docs-only. No TDD mode applies. All verification is goal-based and manual:

- **Flow completeness (manual read-through, per flow):** each flow (A–F) is read cold by a reviewer new to the guide, who follows the flow from the first command to the documented completion signal without consulting any document not explicitly linked from the guide. Any step that is ambiguous or insufficient requires a rewrite. This is the primary verification gate.
- **No-credential scan (goal-based grep):** every example TOML, shell command, and environment variable snippet across all delivered documents is scanned for real hostnames (any host that is not `example.test` or a subdomain thereof), URL user-info (`user:pass@host` pattern), `Authorization:` header values other than environment variable references, and any phrase describing TLS-disable or certificate-ignore options. Zero matches required.
- **Link integrity (goal-based check):** every relative `[text](path)` link across all new and updated guides resolves to an existing file in the repository. Checked by resolving each link path with `test -f`.
- **Diátaxis format conformance (goal-based grep):** the new guide contains the `**Use this when:**`, `**Prerequisites:**`, `**Result:**` header block at the top, and a `## Related` section at the bottom, matching the pattern established in existing shared how-to guides.

## Acceptance Criteria

- [x] `docs/guides/_shared/how-to/use-an-artifactory-catalogue.md` is present and contains all six flows (A–F), each under its own `##` heading.
- [x] Flow A (org bootstrap from fork) documents the complete sequence: fork the catalogue repository; edit `agentbundle/_data/install-defaults.toml` in the fork to set `enabled = true` with all four required fields (`base-url`, `repository`, `bundle`, `channel`) using `example.test` placeholders; distribute the fork — and explicitly states that a developer who installs from the org fork receives the org Artifactory channel at Layer 3 without any manual `agentbundle config set source` step.
- [x] Every `[organization.artifactory]` TOML block in Flow A and in any updated guide shows `enabled = true` alongside all four required fields; no partial or malformed `enabled = true` org block appears in any delivered document.
- [x] Flow B (repo-scope CI upgrade) documents the full sequence: `agentbundle upgrade --all --scope repo --format json --yes`; consuming the JSON stdout for PR annotation; and includes a GitHub Actions YAML snippet with `workflow_dispatch:` trigger and `${{ secrets.AGENTBUNDLE_HTTP_BEARER_TOKEN }}` credential sourcing.
- [x] Flow B explicitly states: `--format json` with a non-interactive terminal requires `--yes`; the JSON document is the sole content on stdout; all progress, warnings, and diagnostics go to stderr.
- [x] Flow B explicitly states: partial failure is disclosed honestly and is not described as a rollback; re-running `upgrade --all` is idempotent (rows already upgraded are reported as `up-to-date`).
- [x] Flow C (user-scope MDM update) documents at least two MDM distribution approaches and names which source precedence layer (Layer 2 or Layer 3) each activates.
- [x] Flow D (source-conflict remediation) reproduces the error shape the CLI emits on a source-conflict refusal and names both recovery paths: (1) `agentbundle upgrade --pack <name> <catalogue>` to migrate the legacy row and record a real canonical source; (2) `agentbundle uninstall --pack <name>` followed by a fresh install.
- [x] Flow D explicitly states that `--force` does not bypass source-conflict refusal.
- [x] Flow E (fully disconnected hosts) documents using a local directory path as the `<catalogue>` argument and states that no outbound network connection is needed for this path.
- [x] Flow F (security controls) explicitly states all of the following: (a) bearer token is supplied via the `AGENTBUNDLE_HTTP_BEARER_TOKEN` environment variable; (b) the token is never persisted in state, never printed to stdout, and never included in exception repr output; (c) Authorization headers are redacted in error messages and logs; (d) cross-origin redirects are refused; (e) the bearer token is never forwarded to a host other than the one in the original request; (f) TLS trust uses the OS/Python CA configuration (`SSL_CERT_FILE`) with no certificate-disable option; (g) `HTTPS_PROXY` and `NO_PROXY` environment variables are honored; (h) there is no background daemon; (i) SHA-256 integrity verification covers the downloaded archive relative to the channel descriptor's declared digest, and a mismatch fails before any install write; (j) extraction rejects path-traversal, absolute paths, symlinks, hard links, device files, and FIFOs.
- [x] `docs/guides/_shared/how-to/install-agentbundle-from-clone.md` is updated with at least one paragraph explaining that an org fork ships `[organization.artifactory]` in `agentbundle/_data/install-defaults.toml`, and that a developer who installs from the org fork receives the org Artifactory channel (Layer 3) without a manual `config set source` step.
- [x] `docs/guides/_shared/reference/agentbundle.md` is updated to document: (a) `--format table|json` flag on `list-installed` and `upgrade`; (b) `upgrade --all --scope repo|user` and its mutually-exclusive constraint with `--pack`; (c) `AGENTBUNDLE_HTTP_BEARER_TOKEN` environment variable with its redaction guarantee; (d) the five-layer source precedence chain (explicit arg → user config → org bootstrap → editable-clone → packaged fallback).
- [x] `docs/guides/_shared/how-to/upgrade-packs.md` is updated to document `upgrade --all --scope <scope>` as the bulk upgrade path, `--format json` for machine-readable output, and includes a pointer to Flow D in the primary guide for source-conflict errors.
- [x] `docs/guides/_shared/how-to/preview-install-or-upgrade.md` is updated to document `agentbundle upgrade --all --scope repo --dry-run` and to state that blocked rows are visible in the dry-run plan before any write is attempted.
- [x] No delivered document (new or updated) contains: a non-`example.test` hostname; URL user-info credentials; a bearer token value other than the environment variable references `$AGENTBUNDLE_HTTP_BEARER_TOKEN` or `${{ secrets.AGENTBUNDLE_HTTP_BEARER_TOKEN }}`; an `enabled = true` org config block with any required field missing; or any description of a TLS-disable option.
- [x] Every relative `[text](path)` link across all delivered documents resolves to an existing file in the repository.
- [x] `use-an-artifactory-catalogue.md` contains the `**Use this when:**`, `**Prerequisites:**`, and `**Result:**` header block at the top, and a `## Related` section at the bottom, matching the Diátaxis how-to pattern of existing shared guides.
- [x] `docs/guides/README.md` "Shared guides — Install & upgrade" bullet list is updated to include a link to `_shared/how-to/use-an-artifactory-catalogue.md`.

## Assumptions

- Technical: This spec is docs-only — no Python source files, no new runtime dependencies (confirmed from task description and RFC-0072 Non-goals).
- Technical: All upstream ini-004 specs (packstate-source-provenance, https-catalogue-channels, source-conflict-install-guard, list-installed-update-status, upgrade-bulk-all, organization-artifactory-bootstrap, package-catalogue-command, artifactory-publishing-workflow) are Clean — spec-mode adversarial review passed (confirmed from task description).
- Technical: The `[organization.artifactory]` block requires exactly four fields when `enabled = true`: `base-url`, `repository`, `bundle`, `channel` (confirmed from RFC-0072 D2 and spec/organization-artifactory-bootstrap).
- Technical: `--force` does not bypass source-conflict refusal — this is structural in spec/source-conflict-install-guard (the helper has no `force` parameter) (confirmed from RFC-0072 D3 and spec/source-conflict-install-guard).
- Technical: Existing shared guides follow the Diátaxis how-to pattern with `**Use this when:**`, `**Prerequisites:**`, `**Result:**` at the top and `## Related` at the bottom (confirmed by reading `install-agentbundle-from-clone.md`, `upgrade-packs.md`, `preview-install-or-upgrade.md`).
- Technical: The guides `_shared/how-to/install-agentbundle-from-clone.md`, `_shared/reference/agentbundle.md`, `_shared/how-to/upgrade-packs.md`, and `_shared/how-to/preview-install-or-upgrade.md` are the correct update targets (confirmed by reading `docs/guides/README.md` "Shared guides" section).
- Product: Six flows (A–F) are the core deliverable; an enterprise adopter completing any flow cold is the success criterion (confirmed from task description and the RFC-0072 Follow-on artifacts list).
- Process: Spec lifecycle is Draft → Approved → Implementing → Shipped (confirmed from `docs/CONVENTIONS.md`).
- Process: The `docs/specs/README.md` already contains a placeholder row for `corporate-update-documentation` (confirmed by reading `docs/specs/README.md` line 27).
