# Plan: Corporate Update Documentation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

All work is guide authoring and targeted prose editing — no source code changes, no build steps, no new dependencies. The deliverable is one new guide, four targeted updates to existing shared guides, and one link entry in the guides index — all in a single PR.

Order of operations:

1. **T1 (primary guide) first.** The new guide (`use-an-artifactory-catalogue.md`) is the anchor all other tasks cross-reference. It is written after verifying CLI surface details against the upstream ini-004 specs to avoid revisions.
2. **T2–T5 (existing guide updates) in any order.** These four tasks are independent of each other and depend only on T1 for the cross-reference link to the primary guide.
3. **T6 (README link) last.** The guides README update is a one-line addition that depends on the primary guide path being confirmed.

The riskiest part of this work is correctly representing CLI behavior — the exact error shape for Flow D, the exact JSON stdout/stderr split for Flow B, and the `--force` non-bypass guarantee for Flow D. These are all defined by upstream specs (all verified Clean before this spec was authored). Any apparent discrepancy between a guide draft and an upstream spec surfaces before writing continues.

## Constraints

- RFC-0072 (follow-on spec deliverable): the governance anchor for this spec as a named follow-on in the RFC's Follow-on artifacts list. RFC-0072 decisions are D1–D6; this spec is not D7.
- spec/packstate-source-provenance: defines `canonicalize_source` and the credential-redaction rules for source strings — referenced in the five-layer source-precedence chain (AC13d/T3) and Flow D's source-conflict remediation.
- spec/https-catalogue-channels: defines `catalogue+https://` and `archive+https://` scheme behavior, bearer token handling, redirect constraints, integrity verification, and extraction-safety properties documented in Flow F.
- spec/organization-artifactory-bootstrap: defines the `[organization.artifactory]` TOML schema documented in Flow A. The four required fields (`base-url`, `repository`, `bundle`, `channel`) and the Layer 3 placement are sourced from this spec.
- spec/source-conflict-install-guard: defines the conflict detection behavior, error shape, `--force` non-bypass (structural: the helper has no `force` parameter), and both recovery paths documented in Flow D.
- spec/upgrade-bulk-all: defines `upgrade --all --scope`, `--format json`, preflight-then-apply, stop-on-first-failure, partial failure semantics, and the `--yes` requirement for non-interactive JSON mutation documented in Flow B.
- spec/list-installed-update-status: defines `--format table|json`, the four status values, and the JSON schema_version 1 output shape documented in the reference update (T3).
- spec/package-catalogue-command: defines the `agentbundle package-catalogue` command that org fork maintainers run before publishing — cross-referenced in Flow A.
- spec/artifactory-publishing-workflow: the sibling docs spec (M5b); the primary guide's Related section cross-references `publish-to-artifactory.md` when that file exists (see T1 approach).
- All hostnames in examples: `example.test` or subdomains only — no real Artifactory instance URLs, no real org names.

## Construction tests

Most verification is per-task. The cross-cutting checks that span all delivered documents:

**Manual verification (cross-cutting):**
- Hostname scan across all six delivered files (one new guide + four updated guides + `docs/guides/README.md`): every URL host in every example must be `example.test` or a subdomain thereof. Use an allow-list approach — flag any host that does not match `([\w-]+\.)*example\.test` — rather than a deny-list regex (deny-lists miss uncommon TLDs and end-of-line positions).
- No-credential scan: no `Authorization:` header containing a non-placeholder token; no `enabled = true` without all four required fields (verifies AC3 across all delivered docs); no URL user-info pattern (`user:pass@host`) anywhere.
- TLS-disable scan: `grep -riE "(--insecure|verify=False|disable.*tls|ignore.*cert|no.verify)" <files>` returns zero matches across all six files (verifies AC16 "no description of a TLS-disable option").
- Link integrity: every relative path in `[text](path)` form across all six delivered files resolves via `test -f <resolved-path>` to an existing file.

**Integration tests:** none — docs-only, no code.

## Tasks

### T1: Author `use-an-artifactory-catalogue.md` with all six flows

**Depends on:** none

**Touches:** `docs/guides/_shared/how-to/use-an-artifactory-catalogue.md`

**Tests:**
- Cold read of each flow (A–F): a reviewer new to the guide follows each flow from the first command to the completion signal without consulting any document not linked from the guide (verifies AC1–AC11).
- Diátaxis header block present (`**Use this when:**`, `**Prerequisites:**`, `**Result:**`) and `## Related` section at bottom (verifies AC18).
- `grep -E "enabled = true" use-an-artifactory-catalogue.md` — every match is followed within the same TOML block by `base-url`, `repository`, `bundle`, and `channel` lines (verifies AC3).
- `grep -Ev "example\.test"` over all URL-bearing lines returns zero non-`example.test` domains (verifies AC16).
- Bearer token appears only as `$AGENTBUNDLE_HTTP_BEARER_TOKEN` or `${{ secrets.AGENTBUNDLE_HTTP_BEARER_TOKEN }}` environment variable references, never as a literal value (verifies AC11a, AC16).
- `--force` described only as non-bypassing in Flow D; no sentence describes `--force` as unlocking a source-conflict refusal (verifies AC9, AC16).

**Approach:**
- Create `docs/guides/_shared/how-to/use-an-artifactory-catalogue.md`.
- Write the Diátaxis how-to header block:
  - `**Use this when:**` — you are an enterprise adopter configuring agentbundle for an internal Artifactory mirror, running CI-driven bulk upgrades, or operating in a network-restricted or MDM-managed environment.
  - `**Prerequisites:**` — agentbundle CLI on PATH (or a local clone with `pip install -e packages/agentbundle/`); for Flows A and C, a fork of the catalogue repository; for Flow B, a CI pipeline with access to `${{ secrets.AGENTBUNDLE_HTTP_BEARER_TOKEN }}`.
  - `**Result:**` — one of six enterprise adoption flows completed, with no undocumented steps.
- Write `## Flow A — Org bootstrap from fork`:
  - Step 1: Fork the catalogue repository.
  - Step 2: Edit `agentbundle/_data/install-defaults.toml` in the fork. Show the TOML block with `enabled = true` and all four required fields using `example.test` values.
  - Step 3: Run `agentbundle package-catalogue` to produce the deterministic archive and channel descriptor (cross-reference `publish-to-artifactory.md` for the upload sequence; include this link only if that file exists at delivery time — see T1 Approach note below).
  - State explicitly: developers who `pip install` from the org fork receive the org Artifactory channel at Layer 3 — no manual `agentbundle config set source` step is needed.
- Write `## Flow B — Repo-scope CI upgrade`:
  - Document `agentbundle upgrade --all --scope repo --format json --yes`.
  - State explicitly: `--format json` with a non-interactive terminal requires `--yes`; the JSON document is the sole content on stdout; all progress, warnings, and diagnostics go to stderr.
  - Include a GitHub Actions YAML snippet with `workflow_dispatch:` trigger, `env: AGENTBUNDLE_HTTP_BEARER_TOKEN: ${{ secrets.AGENTBUNDLE_HTTP_BEARER_TOKEN }}`, and a step that parses stdout JSON for PR annotation (using `jq` or a shell `--format json` consumer).
  - State explicitly: partial failure is disclosed honestly and is not a rollback; re-running `upgrade --all` after a partial failure is safe (already-upgraded rows report `up-to-date`).
- Write `## Flow C — User-scope MDM update`:
  - Path 1 (Layer 3): MDM distributes a pre-configured agentbundle wheel that includes `enabled = true` in `agentbundle/_data/install-defaults.toml`. State this activates Layer 3.
  - Path 2 (Layer 2): MDM distributes a `config.toml` with `[settings]\nsource = "catalogue+https://artifactory.example.test/..."`. State this activates Layer 2 (user config) and takes precedence over Layer 3.
- Write `## Flow D — Source-conflict remediation`:
  - Reproduce the error message shape the CLI emits on a source-conflict refusal (sourced from spec/source-conflict-install-guard).
  - Name both recovery paths: (1) `agentbundle upgrade --pack <name> <catalogue>` — migrates the legacy row and records the real canonical source; (2) `agentbundle uninstall --pack <name>` then reinstall from the intended catalogue.
  - State explicitly that `--force` does not bypass source-conflict refusal.
- Write `## Flow E — Fully disconnected hosts`:
  - Document using a local directory path as the `<catalogue>` argument (e.g. `agentbundle install /path/to/local/catalogue --pack core`).
  - State that no outbound network connection is needed for a local-path catalogue (AC10).
- Write `## Flow F — Security controls`:
  - List all ten security properties from AC11 as a structured reference: bearer token supply, no persistence, redaction, cross-origin redirect refusal, no host-hop forwarding, TLS trust model, proxy variables, no daemon, SHA-256 integrity verification (digest mismatch fails before any write), extraction hardening (path-traversal/symlink/hard-link/device/FIFO rejection).
- Write `## Related` section linking to: `install-agentbundle-from-clone.md`, `upgrade-packs.md`, `../reference/agentbundle.md`. Add a link to `publish-to-artifactory.md` only if that file already exists at delivery time (it is produced by `spec/artifactory-publishing-workflow`, which is a peer spec in the same ini-004 wave); if absent, note it as a follow-on link in the Related section using plain text with no broken `[text](path)` link.

**Note on cross-spec dependency:** the `publish-to-artifactory.md` link in Related is gated on `spec:artifactory-publishing-workflow` shipping before or with this PR. The link itself is not an AC requirement, so AC17 is satisfied either way: include the link and it resolves, or omit the link and AC17 has no broken link to flag.

**Done when:** All primary-guide and cross-cutting ACs (AC1–AC11, AC16–AC18) pass; file is present at the specified path.

---

### T2: Update `install-agentbundle-from-clone.md` with org-fork note

**Depends on:** T1 (cross-reference target must exist)

**Touches:** `docs/guides/_shared/how-to/install-agentbundle-from-clone.md`

**Tests:**
- A section (or callout) is present that explains org-fork bootstrap and Layer 3 behavior (verifies AC12).
- `grep -c "Layer 3" install-agentbundle-from-clone.md` returns ≥ 1 (verifies AC12).
- Link to `use-an-artifactory-catalogue.md` resolves via `test -f` (verifies AC17).
- No non-`example.test` hostname in the new content (verifies AC16).

**Approach:**
- After the "Step 1 — Install the module" section, add a callout or subsection headed "Installing from an org fork":
  - Explain that an org fork ships an `[organization.artifactory]` block in `agentbundle/_data/install-defaults.toml`.
  - State that installing from the org fork (`pip install -e packages/agentbundle/` against the fork) gives the developer the org Artifactory channel at Layer 3 — no `agentbundle config set source` step is needed.
  - Cross-reference Flow A in `use-an-artifactory-catalogue.md` for the full org-bootstrap sequence.

**Done when:** New content present; AC12 passes; link resolves.

---

### T3: Update `agentbundle.md` reference with enterprise CLI surfaces

**Depends on:** T1 (cross-reference target must exist)

**Touches:** `docs/guides/_shared/reference/agentbundle.md`

**Tests:**
- `--format table|json` documented under both `list-installed` and `upgrade` sections (verifies AC13a).
- `upgrade --all --scope repo|user` present with mutual-exclusion note for `--pack` (verifies AC13b).
- `AGENTBUNDLE_HTTP_BEARER_TOKEN` present with redaction guarantee statement (verifies AC13c).
- Five-layer source precedence chain present as a numbered list or table (verifies AC13d).
- All links resolve; no non-`example.test` hostname in new content (verifies AC16, AC17).

**Approach:**
- Update the "See what's installed" section:
  - Add `--format table|json` to the flags table with effect "Emit JSON (schema_version 1) to stdout; all diagnostics to stderr. Default: `table`."
  - Note that `--updates-only` is combinable with `--format json`.
- Update the section covering `upgrade` (or add a dedicated "Bulk upgrade" subsection):
  - Document `upgrade --all --scope repo|user` and state it is mutually exclusive with `--pack`.
  - Document `--format json` behavior: JSON to stdout, `--yes` required for non-interactive terminals.
  - Note stop-on-first-failure and that partial completion is disclosed honestly.
- Add a "Source configuration" section covering:
  - The five-layer source precedence chain as a numbered list: (1) `--catalogue` argument; (2) `[settings].source` in user config; (3) org bootstrap from `[organization.artifactory]` in `install-defaults.toml`; (4) editable-clone detection via PEP 610; (5) packaged `[defaults].source` in `install-defaults.toml`.
  - `AGENTBUNDLE_HTTP_BEARER_TOKEN` environment variable: state it supplies the bearer token for `catalogue+https://` and `archive+https://` sources, is never persisted in state or printed, and is always redacted in error output.
  - Cross-reference Flow F in `use-an-artifactory-catalogue.md` for the full security-controls reference.

**Done when:** All four documentation areas present; AC13 passes.

---

### T4: Update `upgrade-packs.md` with bulk upgrade and source-conflict pointer

**Depends on:** T1 (cross-reference target must exist)

**Touches:** `docs/guides/_shared/how-to/upgrade-packs.md`

**Tests:**
- `upgrade --all --scope <scope>` present in the "Whole pack" section (verifies AC14).
- `--format json` documented for bulk mode (verifies AC14).
- Pointer to Flow D present (verifies AC14).
- All links resolve; no non-`example.test` hostname in new content (verifies AC16, AC17).

**Approach:**
- Under "Whole pack (default)", extend the `agentbundle` CLI subsection to show `upgrade --all --scope repo|user` as the bulk upgrade form, alongside the existing single-pack form.
- Add a note: `--format json` emits a machine-readable JSON document to stdout; pass `--yes` when running in a non-interactive environment.
- Add a "Troubleshooting" note: if `agentbundle install` is refused with a source-conflict error (different source already recorded for that pack name at this scope), follow Flow D in [`use-an-artifactory-catalogue.md`](use-an-artifactory-catalogue.md).

**Done when:** New content present; AC14 passes.

---

### T5: Update `preview-install-or-upgrade.md` with bulk dry-run

**Depends on:** T1 (cross-reference target must exist)

**Touches:** `docs/guides/_shared/how-to/preview-install-or-upgrade.md`

**Tests:**
- `agentbundle upgrade --all --scope repo --dry-run` present in a new "Preview a bulk upgrade" section (verifies AC15).
- Statement that blocked rows appear in the dry-run plan and prevent all writes (verifies AC15).
- All links resolve; no non-`example.test` hostname in new content (verifies AC16, AC17).

**Approach:**
- Add a "Preview a bulk upgrade" section after the existing "Preview an upgrade" section:
  - Show `agentbundle upgrade --all --scope repo --dry-run`.
  - Include example output that includes at least one blocked row (showing the blocked status and reason).
  - State explicitly: blocked rows prevent all writes; the blocked plan is shown in full and the command exits non-zero, without touching the filesystem.

**Done when:** New section present; AC15 passes.

---

### T6: Add Artifactory guide link to `docs/guides/README.md`; flip spec status to Shipped

**Depends on:** T1 (link target must exist)

**Touches:** `docs/guides/README.md`, `docs/specs/corporate-update-documentation/spec.md`, `docs/specs/README.md`

**Tests:**
- `grep "use-an-artifactory-catalogue" docs/guides/README.md` returns ≥ 1 match (verifies AC19).
- Link resolves via `test -f docs/guides/_shared/how-to/use-an-artifactory-catalogue.md` (verifies AC17).
- `docs/specs/corporate-update-documentation/spec.md` Status header reads `Shipped`.
- `docs/specs/README.md` row for `corporate-update-documentation` reads `Shipped`.

**Approach:**
- In the "Shared guides — Install & upgrade" bullet list (currently: from a clone, into Codex, into Kiro, preview with `--dry-run`, upgrade), add `[use an Artifactory-hosted catalogue](_shared/how-to/use-an-artifactory-catalogue.md)` as a new bullet.
- Update `docs/specs/corporate-update-documentation/spec.md` Status to `Shipped`.
- Update `docs/specs/README.md` row status to `Shipped` for this spec.

**Done when:** Link present, resolves, AC19 passes, and spec/README statuses read `Shipped`.

---

## Rollout

Docs-only PR. No deployment sequencing, no infra changes, no external-system integration. All six tasks ship in a single PR. The PR that delivers the guide set marks this spec `Shipped` and updates the `docs/specs/README.md` row status to `Shipped`.

## Risks

- **CLI surface misrepresentation:** the exact error message text for Flow D and the exact JSON output shape for Flow B are defined by upstream specs, not invented here. A discrepancy between a guide draft and the upstream spec surfaces as a verification failure on cold-read. Mitigated by reading each upstream spec before writing the corresponding flow section.
- **Cold-read verification requires a fresh reader:** self-review by the author is insufficient for the flow-completeness check. If only the author is available, a structured substitute is acceptable: phrase each step as a question the reader must be able to answer before proceeding (e.g., "What value does `base-url` take?"), and verify that each question is answerable from within the guide.
- **Diátaxis shape drift in updates:** the four updated shared guides use an established header block pattern. Updates that break the top-of-file format fail the Diátaxis conformance check. Mitigated by reading the existing pattern in each file before editing.

## Changelog

- 2026-07-24: initial plan
