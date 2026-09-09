# Spec: guide invocation and outcome coverage

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full. The slice changes adopter-facing guides and published pack skill
descriptions across multiple independently released packs.

## Objective

A reader can see how to invoke the remaining accepted-base workflows and what
the unfinished product-strategy surfaces leave them with. Published,
user-invocable skills that still lack invocation phrasing show one literal,
source-grounded example request and identify that phrasing with `Triggers on`.
The improvement is measured against a fixed path ledger rather than a corpus
total that changes as the catalogue grows.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing guidance | Applicable — readers need literal requests and explicit results | The guide paths in [`notes/accepted-base.md`](notes/accepted-base.md) | `author-product-docs`; guide owners | Each recorded missing A or D affordance is present and source-grounded | AC1–AC3 hold |
| Published invocation contract | Applicable — skill descriptions are the published routing surface | The `SKILL.md` paths in [`notes/accepted-base.md`](notes/accepted-base.md) | Owning pack maintainers | Every target description carries a quoted request and `Triggers on` | AC4–AC7 hold |
| Release truth | Applicable — `.apm` source changes alter released packs | Owning `pack.toml`, plugin manifest where present, and `docs/product/changelog.md` | Owning pack maintainers | Matching patch-version, plugin version, and changelog evidence | AC8–AC10 hold |
| Accepted scope | Applicable — the corpus and percentages change independently of this slice | [`notes/accepted-base.md`](notes/accepted-base.md) | This spec | Fixed target paths, missing affordances, and exclusions | Every ledger member passes; new corpus files do not expand the slice |
| Execution evidence | Applicable | `notes/verification-ledger.md` | `work-loop` | Before/after audit rows, quality review, projection, and gate results | Closeout verifies AC1–AC16 from recorded evidence |
| Architecture and API contracts | Not applicable — no runtime boundary or schema changes | — | — | — | — |

## Boundaries

### Always do

- Copy or adapt invocation wording from the target skill, its owning guide,
  journey contract, or another current repository-owned behavior source; record
  that source in the verification ledger.
- Preserve each guide's Diataxis kind and make the added request or outcome fit
  that kind rather than turning references and explanations into tutorials.
- Edit `.apm` skill sources, then refresh generated/self-hosted projections by
  the repository's normal pack build path.
- Keep pack/plugin versions and release history aligned with every changed
  published skill source.

### Ask first

- Reclassifying a target as ineligible after this spec is approved.
- Changing an invocation's behavioral meaning rather than expressing behavior
  already owned by the skill or guide.
- Changing the audit detector or the guide schema.

### Never do

- Add invocation copy to deprecated aliases or internal/reference-only skills
  listed as deliberate exclusions in the accepted base.
- Edit generated skill projections or generated docs as source.
- Deliver experience-design uplift, a new cross-pack digital-product tutorial
  or intent index, or new role-specific first-value, safety, recovery, or
  evaluation content.
- Assert a fixed repository-wide guide or skill count as the completion test.

## Testing Strategy

- **Goal-based audit checks:** rerun `tools/audit-guide-affordances.py` with a
  fresh ledger. Every guide/affordance cell recorded in the accepted base must
  have evidence, and every skill target must report both a quoted example and
  `Triggers on`. Compare exact path membership, not aggregate counts.
- **Goal-based source checks:** validate that every quoted utterance is in the
  skill `description:` field and that every changed published pack has matching
  source/plugin version and changelog treatment.
- **Goal-based integration checks:** run the pack verification and self-hosting
  path, then build the site so published projections are derived from source.
- **Documentation review:** apply `author-product-docs` to every guide change
  and compare representative additions with the established conversation-first
  standard. The verification ledger records the source for each phrase and
  outcome; regex presence alone is insufficient.

No runtime logic changes, so TDD is not the primary mode. No new screen or
interaction is introduced, so visual QA is not required.

## Acceptance Criteria

- [ ] **AC1 — accepted guide invocation gaps close.** Every guide row marked A
      in [`notes/accepted-base.md`](notes/accepted-base.md) contains a literal,
      copy-pasteable request after implementation.
- [ ] **AC2 — accepted outcome gaps close.** Every guide row marked D in the
      accepted base states the concrete artifact, decision, or next usable state
      the reader holds.
- [ ] **AC3 — guide additions match their sources.** Each added request and
      outcome matches behavior stated by the current repository-owned source
      named for it in the verification ledger.
- [ ] **AC4 — accepted skill phrase gaps close.** Every skill-description path
      in the accepted base contains a single-line paired-quote user request in
      its published `description:` field that
      `tools/audit-guide-affordances.py` records as quoted-example evidence.
- [ ] **AC5 — skill triggers are explicit.** Every skill-description target in
      the accepted base contains the literal phrase `Triggers on` inside its
      published `description:` field.
- [ ] **AC6 — skill requests route to existing behavior.** Each added quoted
      request asks for a job the target skill already handles, as shown by the
      current skill, guide, or journey source named in the verification ledger.
- [ ] **AC7 — routing copy does not change authority.** No accepted skill target
      changes an instruction below its frontmatter or changes a declared tool,
      permission, confirmation, or authority boundary.
- [ ] **AC8 — changed packs receive a patch release.** Every published pack
      whose `.apm` source changes keeps the accepted major and minor components
      and has a patch component exactly one greater than its accepted-base
      version.
- [ ] **AC9 — matching plugin versions stay equal.** For every changed pack
      that publishes a matching plugin, its plugin version equals its pack
      version.
- [ ] **AC10 — release history names every changed pack.**
      `docs/product/changelog.md` records the invocation-phrasing change for
      each changed published pack.
- [ ] **AC11 — catalogue verification accepts the sources.** The catalogue
      verification command completes successfully after the source and release
      metadata changes.
- [ ] **AC12 — self-hosted projections derive from source.** The repository
      self-host command completes from the changed `.apm` sources.
- [ ] **AC13 — canonical guides generate.** `tools/build-site.py` completes
      from the changed guide and pack sources.
- [ ] **AC14 — the web prerequisite builds.** The web build completes after
      guide generation.
- [ ] **AC15 — the documentation site builds in order.** The documentation-site
      build completes after the web build.
- [ ] **AC16 — measured coverage moves forward without regressions.** For each
      of A, D, quoted-example, and `Triggers on`, the post-implementation set of
      present guide or skill paths contains every pre-implementation present
      path and every applicable accepted-base target.

## Follow-ons

- `docs/product/intents/experience-design-delivery-packet.md`: experience-design
  guide uplift after its research-first assumptions resolve.
- `docs/product/intents/digital-product-guides-update.md`: cross-pack tutorial
  and per-pack intent indexes.
- `docs/product/intents/nontechnical-pack-first-value-rollout.md`: new
  role-specific first-value, safety, recovery, and evaluation content.

## Assumptions

- Technical: `tools/audit-guide-affordances.py` supplies traceable A–E guide
  evidence and published-skill phrase evidence (source:
  `tools/audit-guide-affordances.py`; probe 2026-09-09).
- Technical: `guides/**` and pack `.apm` trees are canonical sources; generated
  documentation and self-hosted skill projections are derived outputs (source:
  `guides/AGENTS.md`, `packs/AGENTS.md`).
- Process: published `.apm` changes require pack/plugin version alignment,
  changelog treatment, evaluation updates where affected, and self-hosting
  (source: `packs/AGENTS.md`, `docs/CONVENTIONS.md`).
- Product: close every eligible accepted-base target while excluding the three
  related-intent boundaries recorded above (source: user confirmation
  2026-09-09).
