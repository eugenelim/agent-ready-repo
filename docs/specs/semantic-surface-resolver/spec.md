# Spec: Shared semantic-surface resolver

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096; RFC-0083; RFC-0093; RFC-0094; ADR-0077; ADR-0078
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/semantic-surface-resolution.schema.json`, `contracts/jsonschema/workspace-entry.schema.json`
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter or core workflow resolves a requested semantic role to the destination that its repository actually owns without assuming catalogue paths, Markdown, `workspace.toml`, a mandatory configuration file, or an installed shaping pack. One shared, read-only resolver applies the RFC-0096 precedence order to explicit, repository-policy, established in-repository, and established external candidates; reports locator, provenance, evidence strength, availability, writability, confinement, authority, revision, and required confirmations; and fails closed on ambiguity, contradiction, unsafe local paths, or missing destinations. This Wave 1 surface supplies the additive contract and locator/evidence fixtures that later waves consume without changing delivery lifecycle behavior.

## Boundaries

### Always do

- Preserve adopter-owned paths, established conventions, optional configuration adapters, and external locators as first-class evidence.
- Resolve local repository paths by canonicalizing the repository root and candidate, then proving the resolved candidate remains inside the root before any read or write.
- Keep source, write, and deletion authority independent and report unknown authority explicitly.
- Treat candidate descriptions, repository prose, external locators, and configuration values as untrusted data; consume only closed contract fields.
- Keep discovery bounded: callers supply at most 32 candidates with at most four evidence records each, and structural convention evidence cites no more than two analogues plus their tests or construction path.
- Preserve `workspace-entry.v1` path entries byte-for-byte in meaning while accepting the additive role/locator extension.

### Ask first

- Ask before selecting among equally ranked policy-permitted candidates or accepting an inferred convention as established.
- Ask before changing the role vocabulary, precedence order, evidence-strength vocabulary, locator representation, or authority dimensions.
- Ask before making a locator-only workspace entry dispatchable or changing any lifecycle collection, status, or transition.
- Ask before introducing a mandatory repository configuration file, global surface registry, external network lookup, or dependency.

### Never do

- Never create, move, copy, or delete a resolved destination as part of resolution.
- Never let an explicit destination override mandatory repository policy.
- Never infer an established convention from one example, contradictory evidence, comments, summaries, list order, tracker labels, or prior-session memory.
- Never coerce an external locator into a local path, fetch it, probe credentials, or claim availability, writability, or authority without evidence.
- Never begin RFC-0096 Waves 2–7, add closeout/cooling/retirement behavior, or alter `work-loop` lifecycle ownership.
- Never add a new top-level directory, runtime dependency, tracker adapter, or second competing resolver.

## Testing Strategy

- **Resolution precedence and evidence invariants: TDD.** Table-driven unit tests exercise each precedence rung, mandatory-policy rejection, duplicate-equivalent candidates, ambiguity, contradiction, absence, bounded candidate/evidence limits, and authority independence because these are compressible pure-function rules.
- **Repository confinement and external-locator separation: TDD with real filesystem fixtures.** Temporary repositories exercise valid local paths, missing future targets, absolute/traversing/backslash/drive paths, symlink escapes, and symlink loops; external fixtures prove zero filesystem and network access.
- **Published contracts and compatibility: TDD at the schema boundary.** JSON fixtures validate the resolution contract and the additive workspace-entry path-or-locator shape; legacy path fixtures retain their normalized meaning and locator-only entries remain non-dispatchable in Wave 1.
- **Portable projection and activation: goal-based checks.** Core pack tests, catalogue lint/verify, self-host projection, and work-intake evaluation cases prove the source implementation and all installed projections agree.
- **Completion evidence: goal-based fixture matrix.** One deterministic matrix records explicit, repository-policy, custom convention/configuration, external, ambiguous, absent, and unsafe-local outcomes with the complete provenance/authority result.

## Acceptance Criteria

- [x] **AC1 — Published resolution contract.** `contracts/jsonschema/semantic-surface-resolution.schema.json` is a closed JSON Schema Draft 2020-12 contract with `contract_version = semantic-surface-resolution.v1` and an `x-spec` backlink to this spec.
- [x] **AC2 — Semantic roles.** The contract and runtime share the exact portable role vocabulary: `delivery-brief`, `delivery-contract`, `current-product-truth`, `user-documentation`, `product-history`, `release-history`, `current-architecture`, `architecture-design`, `decision-record`, `operations`, `interface-contract`, `project-knowledge`, and `runtime-coordination`; filenames and formats are not roles.
- [x] **AC3 — One precedence algorithm.** The resolver selects the first unique policy-permitted candidate from: explicit destination; declared repository policy/configuration; established in-repository convention; established external destination. An explicit candidate that violates mandatory policy is refused, equivalent candidates collapse by canonical identity, and lower-ranked evidence never overrides a unique higher-ranked result.
- [x] **AC4 — Bounded evidence, not repository-wide discovery.** The runtime accepts only closed candidate records supplied by a caller, rejects more than 32 candidates or four evidence records per candidate, performs no recursive repository scan or network access, treats one analogue as inference only, and requires confirmation before inferred or contradictory convention evidence can resolve.
- [x] **AC5 — Optional adapters.** Repository-specific configuration adapters may emit the same closed candidate records, but the resolver works with no adapter, requires no configuration file or global `[surfaces]` registry, and gives configuration evidence no authority beyond its declared policy strength.
- [x] **AC6 — Fail-closed repository confinement.** A repository-path locator rejects empty, absolute, drive-qualified, backslash-based, dot-segment, symlink-escaped, and symlink-looping paths; it resolves the repository root and candidate and proves containment before reporting a local physical locator. Resolution uncertainty returns a stable refusal without raw exception text.
- [x] **AC7 — External locators stay external.** An external locator is preserved as a non-path logical/physical locator, rejects credentials and query/fragment material, never enters `Path` resolution, and triggers no HTTP, DNS, tracker, shell, or credential operation.
- [x] **AC8 — Complete result and independent authority.** A resolved result reports role; logical and physical locator; provenance and evidence strength; availability, writability, and confinement; source, write, and deletion authority independently; revision or fingerprint when known; and confirmations. Unknown facts remain `unknown` and one authority dimension never implies another.
- [x] **AC9 — Ambiguity, contradiction, and absence.** Equally ranked non-equivalent candidates return `confirmation-required`; contradictory mandatory policies and unsafe candidates return `refused`; no candidate returns `destination-required` with an offer-shaped next action. Every non-resolved result omits logical/physical locators and revision/fingerprint, carries decision provenance, and reports availability, writability, confinement, and all three authority dimensions as `unknown`; none selects a destination or mutates state.
- [x] **AC10 — Additive workspace locator extension.** `workspace-entry.v1` retains every valid legacy `path` entry and additionally accepts `surface_role` plus a closed non-path `locator`. An entry supplies at least one of `path` or `locator`; locator-only entries require `surface_role`, are parsed without local path access, and remain visible but non-dispatchable with the existing `configuration_mismatch` finding until a later wave explicitly integrates them.
- [x] **AC11 — No lifecycle behavior change.** Resolution is read-only and does not create artifacts, register workspace entries, change lifecycle membership/status, pause work, mark closeout, produce completion receipts, cool, retain, reclassify, retire, or delete.
- [x] **AC12 — Provenance and authority survive every surface.** Contract fixtures, Python results, safe rendered output, and projected installed code preserve the same role, canonical locator identity, evidence source/strength, revision/fingerprint, confinement, and three authority dimensions without raw exception text, credentials, personal data, or embedded instructions. Logical/physical locators, provenance references, authority evidence references, confirmations, and workspace source references reject credential-bearing, query/fragment-bearing, whitespace/control-bearing values before rendering or consumption.
- [x] **AC13 — RFC-0096 Wave 1 fixture evidence.** A committed deterministic fixture matrix covers explicit local, mandatory repository policy, confirmed custom convention, optional configuration adapter, established external destination, equivalent aliases, ambiguity, absence, mandatory-policy conflict, unsafe path, symlink escape, and symlink loop; each case asserts the full status/locator/evidence/authority result and zero mutation.
- [x] **AC14 — Portable release gates.** Relevant contract, resolver, workspace parser, work-intake, projection, and eval tests pass along with core pack lint/verify and self-host checks; core pack/plugin versions move together under the repository release rule and the changelog names only Wave 1 behavior.

## Assumptions

- Technical: Python 3.11+ stdlib is the portable core runtime. (source: `packs/core/pack.toml`)
- Technical: `workspace-entry.v1` is the current repository index contract and legacy `path` remains supported. (source: `contracts/jsonschema/workspace-entry.schema.json`; user confirmation 2026-08-23)
- Technical: the interface is a standalone JSON Schema at `contracts/jsonschema/semantic-surface-resolution.schema.json` with a stdlib resolver owned by `work-intake`. (source: user confirmation 2026-08-23)
- Technical: `workspace-status` is the current typed workspace reader and the existing `configuration_mismatch` finding is the fail-closed Wave 1 projection for locator-only entries. (source: `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`)
- Product: Wave 1 ends at the resolver, additive locator contract, and locator/evidence fixtures; Waves 2–7 and lifecycle mutation are excluded. (source: RFC-0096 §9; user confirmation 2026-08-23)
- Product: adopter conventions, optional configuration, external locators, provenance, authority reporting, and repository confinement are required outcomes. (source: user confirmation 2026-08-23)
- Process: structural/public-interface and filesystem-boundary triggers require full work-loop mode with spec-stage adversarial and secure-design review. (source: `AGENTS.md` and `packs/core/AGENTS.md`)
- Process: non-cosmetic core changes update matching pack/plugin versions and the affected evaluation harness. (source: `packs/AGENTS.md`)
