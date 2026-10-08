# Spec: Capture-work alias removal

- **Status:** Approved
- **Owner:** Core work-intake maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0083](../../rfc/0083-work-intake-and-artifact-routing.md), including its 2026-10-02 Errata
- **Brief:** none
- **Discovery:** `intent:capture-work-alias-removal`
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects
> them in place as the work teaches, without an amendment and without a review
> round. A review finding against working material is advisory — it cannot
> block, because nothing gates the text it cites.

## Outcome

Core adopters use `work-intake` as the only supported public intake name, and ordinary workspace reconciliation evaluates only canonical lifecycle entries. Core 3.0.0 contains no `capture-work` skill or accepted-legacy compatibility reader while explicit migration evidence and ledger-backed rollback records remain intact.

## What Changes

- The `capture-work` skill, its activation evals, and its Core pack registration are removed from the authored Core surface.
- Ordinary `workspace-status` reconciliation stops accepting RFC-0083 section 10 legacy shapes as compatibility memberships; explicit migration and rollback paths retain only the parsing needed for reviewed repair operations.
- Core adopter guidance, maintainer guidance, architecture, pack navigation, and journey records describe `work-intake` and canonical workspace entries as the current surface.
- Core pack and plugin metadata move to 3.0.0, the release history records the breaking removal, and self-hosted projections are regenerated from authored sources.
- The AgentBundle package-data runtime is synchronized from the changed workspace-status engine, with its package version owners and release evidence updated under the package release process.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | The public intake name and legacy-workspace recovery route change. | `guides/core/README.md`, `guides/_shared/how-to/use-work-intake.md`, `guides/core/how-to/capture-work.md`, and linked routing references | Core documentation maintainers | Current-guide audit, guide validators, and rendered-link checks | Current guidance invokes only `work-intake`; the retained migration guide is framed as explicit recovery rather than an ordinary reader contract. |
| Current architecture | Ordinary reconciliation and explicit repair no longer share one accepted-legacy contract. | `docs/architecture/work-intake-and-artifact-routing.md` and `packs/core/DESIGN.md` | Core work-intake maintainers | Focused reconciliation and migration regression suites | Both documents name the canonical ordinary-read boundary and the retained explicit repair boundary without describing the alias as installed. |
| Maintainer procedure | Release and rollback require refreshed evidence and fresh authorization. | `docs/guides/reference/work-intake-maintenance.md` | Core work-intake maintainers | Candidate evidence checklist and authorization record | The procedure points maintainers to the Core 3.0.0 removal evidence, release gate, and selected rollback target. |
| Pack navigation | Installed skill inventory and journey metadata change. | `packs/core/README.md`, `packs/core/JOURNEY.md`, and `packs/core/docs/index.md` | Core pack maintainers | Pack tests and self-host verification | No current Core inventory or journey advertises `capture-work`, and `work-intake` remains discoverable. |
| Packaged runtime | AgentBundle ships the workspace-status engine as package data. | `packages/agentbundle/agentbundle/_data/workspace_status_engine.py` and the package version owners | AgentBundle maintainers | Package tests, built-artifact byte comparison, and package release evidence | The published package contains the Core 3.0.0 candidate engine and both package version owners identify that release. |
| Release history | The delivery removes a published primitive in a major release. | `docs/product/changelog.md` | Core release maintainer | Matching pack/plugin versions and a released Core 3.0.0 entry with a `Highlights` disposition | The release entry names the removed alias and ordinary legacy reader, the canonical replacement, and the recovery route. |
| Removal evidence | RFC-0083 requires fresh, check-before-effect authorization over the exact candidate. | `docs/specs/capture-work-alias-removal/notes/verification-ledger.md` | Core work-intake maintainers and RFC-0083 Approver | Exact candidate identity, evidence results, rollback target, and authorization decision | The ledger records a current passing checklist and fresh authorization before Core 3.0.0 is published. |

## Agent Rules

The three-tier guard keeps an implementing agent inside the accepted removal.

### Always do

- Edit `packs/core/.apm/` sources and regenerate projections; never treat an installed adapter projection as the source.
- Keep ordinary reconciliation fail-closed for every former accepted legacy shape while preserving canonical-entry behavior.
- Run the RFC-0083 fixture, writer, seed, guide, migration, recovery, and rollback evidence against the exact release candidate.
- Preserve migration ledgers, canonical artifacts, artifact receipts, and exact rollback bytes.

### Ask first

- Change any migration selection, authorization, ledger, apply, recovery, or rollback contract.
- Remove more than `capture-work`, including `author-brief`, `receive-brief`, or any other compatibility surface.
- Use a Core release other than 3.0.0 or a rollback target other than the dual-reader release named in the fresh RFC-0083 authorization.
- Publish, merge, or otherwise make the compatibility removal effective before the RFC-0083 Approver authorizes the exact candidate.

### Never do

- Edit the shipped `work-intake-migration-docs` spec or the accepted RFC-0083 body to make the removal pass.
- Delete or rewrite canonical artifacts, migration ledgers, authorization records, artifact receipts, or Git history.
- Preserve an ordinary accepted-legacy reader through a renamed helper, alternate alias, new parser module, or hidden fallback.
- Add a new top-level directory, dependency, migration schema, or module boundary for this removal.
- Treat a passing release clock, version bump, build, or spec approval as a substitute for the remaining RFC-0083 gates.

## Testing Strategy

- **Published alias removal (AC-0001, AC-0002):** goal-based checks over the authored Core inventory, pack tests, eval inventory, journey metadata, and self-hosted adapter builds prove that `capture-work` is absent while `work-intake` remains.
- **Ordinary reader removal (AC-0003):** TDD against `run_canonical_reconciliation` uses every RFC-0083 section 10 legacy shape plus a canonical positive control; one validated red stub is carried by plan task T1.
- **Explicit migration preservation (AC-0004, AC-0005):** goal-based integration checks run the existing migration-planning, apply, recovery, and rollback suites because these are retained behaviors rather than new callable surfaces.
- **Remaining compatibility evidence (AC-0006):** goal-based checks run the historical AC14 fixture/writer/seed evidence against the exact candidate without copying its evidence definition into this spec.
- **Current documentation (AC-0007, AC-0008, AC-0012):** goal-based current-surface, guide, and rendered-link checks reject instructional alias use, stale installed-compatibility claims, and broken navigation.
- **Release and projection integrity (AC-0009, AC-0010, AC-0011):** goal-based version, explicit major-successor, changelog, required local gate, catalogue, self-host, and parity checks compare authored sources with generated outputs.
- **Fresh authorization and coordinated release (AC-0013, AC-0014):** manual QA records the RFC-0083 Approver's decision before release, then goal-based registry and artifact checks bind the published Core and AgentBundle versions to the authorized candidate.
- **Stub coverage:** one TDD stub covers AC-0003; AC-0001, AC-0002, AC-0004–AC-0012, and AC-0014 use goal-based checks; AC-0013 uses manual QA.

## Acceptance Criteria

- [ ] **AC-0001.** The authored Core skill inventory contains `work-intake` and contains no `capture-work` skill directory, manifest entry, activation eval, or alias-specific runtime branch.
- [ ] **AC-0002.** A clean self-host build installs and advertises `work-intake` but produces no `capture-work` skill in any supported adapter projection or Core journey inventory.
- [ ] **AC-0003.** For every legacy shape in RFC-0083 section 10 item 2, ordinary canonical reconciliation returns no accepted legacy membership, emits no `legacy_entry` result, and remains non-dispatchable as `unsupported_legacy`; the same run evaluates a canonical target entry through the existing canonical path.
- [ ] **AC-0004.** The explicit migration planner still recognizes every accepted historical legacy fixture and produces the existing reviewed, non-dispatchable migration finding without creating or changing repository state.
- [ ] **AC-0005.** Existing apply, interruption recovery, and rollback integration tests pass unchanged in outcome: rollback restores the exact recorded legacy workspace bytes and leaves canonical artifacts, receipts, and the migration ledger intact.
- [ ] **AC-0006.** The fixture, current-writer, and workspace-seed checks identified by the historical AC14 evidence definition all pass against the Core 3.0.0 candidate.
- [ ] **AC-0007.** Current user guidance contains no instruction or example that invokes `capture-work`; it directs intake requests to `work-intake` and limits legacy-shape handling to the explicit migration and rollback procedure.
- [ ] **AC-0008.** Current architecture, maintainer, pack, and journey documentation describes canonical entries as the ordinary read contract and does not claim that the `capture-work` alias or accepted-legacy compatibility reader remains installed.
- [ ] **AC-0009.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` both declare version `3.0.0`; the Core 3.0.0 changelog entry records the breaking removal with a `Highlights` disposition; and the Core release checker accepts that exact next-major successor through an explicit major-release mode while preserving its default patch-successor checks.
- [ ] **AC-0010.** The repository's required local lint and type gate passes against the Core 3.0.0 candidate.
- [ ] **AC-0011.** Self-host regeneration and catalogue verification produce adapter and packaged-runtime outputs that match the authored Core sources with no subsequent generated drift.
- [ ] **AC-0012.** Current guide, journey, site-generation, and rendered-link validation passes for the maintained documentation surfaces changed by this removal.
- [ ] **AC-0013.** Before Core 3.0.0 is published, the verification ledger records fresh RFC-0083 Approver authorization bound to the exact candidate identity, release version, passing evidence checklist, and selected dual-reader rollback target.
- [ ] **AC-0014.** Release closeout records the authorized `main` commit whose Core manifests and changelog identify 3.0.0, plus the synchronized AgentBundle package released from that same commit; the AgentBundle version tag is pushed immediately after the version-bumping merge, and the published package's workspace-status engine bytes match the authorized candidate. Core is repo-only, so no Core registry receipt is required.

## Follow-ons

none

## Assumptions

none
