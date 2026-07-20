# Spec: OWASP AST10 pack compliance

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Mode:** Full (security-boundary risk trigger)
- **Owner:** eugenelim

**Objective:** Audit all non-core packs against OWASP Agentic Skills Top 10 v1.0 (AST01–AST10), fix all findings, update the security architecture doc to record compliance, and extend the catalogue-curation assimilation skills to include the AST check for ingested primitives.

**Risk triggers:** Security boundary (touches security review, SKILL.md authoring), multi-feature (14 packs + docs).

## Acceptance Criteria

- [x] AC1 — AST audit completed for all non-core packs (14 packs, ~60 skills)
- [x] AC2 — AST05 finding fixed: `research` skill explicitly states fetched content is data not instructions
- [x] AC3 — AST06 finding fixed: `confluence-crawler` and `jira` skills note SSRF containment for user-supplied base URLs (agent pre-flight check; scripts validate scheme only — see AC9 note)
- [x] AC4 — AST10 finding fixed: all non-credentialed boundary-crossing skills carry `metadata.boundaries` in SKILL.md frontmatter
- [x] AC5 — Catalogue-curation `assimilate-primitive` extended with explicit AST01-AST10 security review step in Phase 1
- [x] AC6 — `assimilate-repo` updated to note the AST check flows through `assimilate-primitive` per-unit safety
- [x] AC7 — `docs/architecture/security.md` updated with pack compliance record section
- [x] AC8 — `make build-self` passes clean (projected skills regenerated)
- [x] AC9 — The atlassian SSRF notes (AC3) introduce a new **agent pre-flight host check** — this is a deliberate behavior addition (not documentation-only) required for AST06 compliance. All other changes are metadata/documentation additions only with no logic change.

## Tasks

1. Fix AST05: add untrusted-data posture to `research` skill
2. Fix AST06: add SSRF notes to `confluence-crawler` and `jira` skills (agent pre-flight check; scripts validate scheme only, not private IP ranges)
3. Fix AST10: add `metadata.boundaries` to boundary-crossing skills — `assimilate-primitive`, `assimilate-repo`, `export-catalogue`, `propose-catalogue-pack` (catalogue-curation); `file-to-markdown`, `msg-to-markdown`, `markdown-to-docx`, `markdown-to-html`, `markdown-to-pptx`, `markdown-to-xlsx`, `mermaid-renderer` (converters); `release-loop` (release-engineering); `research`, `source-map` (research)
4. Catalogue-curation update: add AST01-AST10 check step to `assimilate-primitive` Phase 1
5. Update `docs/architecture/security.md` with compliance record
6. Run `make build-self`, verify clean

## What is NOT changing

- Skill logic for non-atlassian skills (metadata/documentation additions only)
- Credentialed skills (already have security metadata via `metadata.credentialed: true`)
- Core pack (out of scope per request)
- Build pipeline or package code

## Findings record

| Finding | Severity | AST | Affected skills | Status |
|---|---|---|---|---|
| research fetched content not marked as untrusted data | Concern | AST05 | research | fixed |
| confluence-crawler/jira base URL lacks SSRF containment declaration | Concern | AST06 | confluence-crawler, jira | fixed |
| Non-credentialed boundary-crossing skills have no security metadata | Concern | AST10 | assimilate-primitive, assimilate-repo, export-catalogue, propose-catalogue-pack, file-to-markdown, msg-to-markdown, markdown-to-docx, markdown-to-html, markdown-to-pptx, markdown-to-xlsx, mermaid-renderer, release-loop, research, source-map | fixed |
| assimilate-primitive Phase 1 lacked explicit AST01-AST10 review | Concern | AST01-AST10 | assimilate-primitive | fixed (catalogue-curation requirement) |

## Passing checks (no action required)

| Check | Result | Notes |
|---|---|---|
| AST01 Malicious content | PASS | No identity-overwrite or credential-camouflage instructions in any skill |
| AST02 Supply chain | PASS | Covered by supply-chain module; pack.toml pinning |
| AST03 Permission over-declaration | PASS | All skills appropriately scoped to stated purpose |
| AST04 Insecure metadata parsing | PASS | Metadata parsed by build pipeline, not skill bodies |
| AST07 Version drift | PASS | Pack-level version pinning via pack.toml |
| AST08 Poor scanning | PASS | Covered by three-bucket delegation taxonomy |
| AST09 Governance | PASS | marketplace.json + install-state-visibility + agentbundle uninstall path |
