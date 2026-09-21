# ADR-0120: Layout-config resolution follows RFC-0096 § 4, not RFC-0040's pack-default tail

- **Status:** Accepted
- **Date:** 2026-09-21
- **Areas:** contracts, governance, packaging
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0030 D3,D8
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0096 (§ 4 "Repository-surface resolution" — the order this record ratifies); RFC-0040 (the pack-default resolution tail this record declines to govern by); ADR-0030 (the layout contract this amends — its `Revisit if:` fourth-consumer trigger opened this record); RFC-0050 (D6 superseded by this record — recorded in that RFC's `## Errata`); ADR-0078 (ratifies core as a `[core]` consumer)

## Decision summary

- **Decision:** We will resolve every pack's durable output path by RFC-0096 § 4's single precedence order, and RFC-0040's pack-default resolution tail will not govern.
- **Because:** three of the seven consumers already implement § 4 and none implements RFC-0040's pack-default step, so § 4 is the order the tree actually runs.
- **Applies to:** resolution of `agentbundle-layout.toml` by every consumer, and the prompt-only boundary in ADR-0030 D8. Not the file's creation or install-time writing, which stay with ADR-0030 D9 and `docs/architecture/agentbundle.md` § 7.2.
- **Tradeoff accepted:** RFC-0040 and RFC-0050 D6 stay readable as accepted records while no longer governing, so a reader who finds either first gets the wrong order until they reach the erratum pointer.
- **Revisit if:** a consumer needs a silent default with no confirmation step, or `semantic-surface-resolution.v1` changes the tiers it returns.

## Context

Two accepted records give different precedence orders for the same resolution, and nothing reconciles them.

RFC-0040's resolution tail (`:193-198`) is: read the `[<pack>]` table, fall back to the **pack's own default** base, then elicit. RFC-0096 § 4 (`:99-105`) is later and heavier, and states that "Every requested surface uses one precedence order": explicit destination; declared repository policy or configuration; established in-repository convention; established external destination; ambiguity requiring confirmation; absence producing an offer to select or create. It has **no pack-default step**.

ADR-0030 `Revisit if:` (`:111`) names the trigger: "a fourth consumer is proposed, which is the moment to re-check the load-bearing assumption behind the three-consumer scope (D3)". Applying one criterion — a pack whose path resolution reads a table of `agentbundle-layout.toml` — there are **seven** consumers, not the three D3 scoped: `architect`, `desk-research`, `product-engineering`, `product-strategy`, `experience-design` (all five declaring `[pack.layout]` in `pack.toml`), `core` (ratified by ADR-0078 `:126-128`; reads `[traceability]` in `lint-traceability.py:225` and documents `[product]` in `workspace-status/references/agentbundle-layout.md`), and `frontend-engineering` (`SKILL.md:66` resolves the `[design]` table experience-design declares, without declaring one of its own). The trigger is met several times over.

Conformance is one-sided. `architect-design/SKILL.md:312-317` carries § 4's order in substance and demotes a repo-root `[architecture] output_dir` to "only optional candidate evidence". `desk-research-project-start` and experience-design's five artifact-writing skills all resolve config, then elicit, with an explicit "never a silent default". No consumer implements RFC-0040's pack-default step. The order with two accepted RFCs behind it is also the order already running.

How the file is created, and which tier a session may read, is owned by `docs/architecture/agentbundle.md` § 7.2 and is not restated here.

## Decision

We will treat RFC-0096 § 4's precedence order as the single governing order for layout-config resolution.

- **D1:** RFC-0096 § 4's six-step order governs repository-surface resolution for every `agentbundle-layout.toml` consumer. RFC-0040's resolution tail does not govern.
- **D2:** There is no pack-default resolution tier. A pack's `[pack.layout.repo] output_dir` is an **install-time seed** under ADR-0030 D9 — the value the installer appends into an adopter's file — and enters resolution only once written there, at § 4 step 2 as declared configuration. It is never a silent runtime fallback ahead of confirmation.
- **D3:** Absence resolves by § 4 steps 5 and 6 — confirmation, then an offer to select or create. The "never a silent default" behaviour already shipped by `desk-research` and `experience-design` is conformant and is not to be changed.
- **D4:** ADR-0030 D8's prompt-only boundary binds an **authoring skill's placement path**. It does not bind a verification lint or a Core resolver capability. `lint-traceability.py`'s `tomllib` read of `[traceability]` (`:225`, feeding `resolve_base` tier 1) is therefore conformant and keeps its adopter configurability.
- **D5:** The consumer set is open. ADR-0030 D3's three-consumer scope is superseded: a pack becomes a consumer by resolving a table, and needs no amendment here to do so.

## Decision drivers

- **Shipped conformance.** Which order the consumers already implement, counted under one criterion applied to every pack.
- **Cost to standing evidence.** Whether adopting the order reds a standing test or contradicts a Shipped acceptance criterion.
- **Recency and weight.** RFC-0096 is later and carries the heavier surface-resolution contract.
- **Adopter stability.** Whether the order forces a rename or relocation of an adopter-owned table.

## Consequences

**Positive:**
- No code change. Every consumer that resolves today is already conformant, so the decision ratifies the tree rather than migrating it.
- No standing test is red and no Shipped acceptance criterion is contradicted. The six Shipped `m2-*` specs that ratify elicitation, and `test_desk_research_project_start_elicitation.py`, all describe § 4 steps 5 and 6 behaviour.
- D4 closes the `lint-traceability.py` question that left ADR-0030 D8 meaning two things, which is how `docs/specs/intake-intent-configured-destination/` was drafted with a code-side read on 2026-09-20 and had to be redesigned.
- The consumer set stops being a fixed list that silently goes stale, which is what produced both the "three consumers" and "six consumers" counts.

**Negative:**
- RFC-0040 and RFC-0050 D6 remain accepted and readable while no longer governing. The erratum pointer on RFC-0050 mitigates this for D6; RFC-0040's tail is mitigated only by this record.
- D4 qualifies a boundary that ADR-0030 D8 stated without qualification, so a reader of D8 alone still gets the unqualified sentence.
- RFC-0050 D6's `[experience]` table name was never implemented — `experience-design/pack.toml:39` declares `section = "design"`, and `frontend-engineering` reads `[design]` cross-pack. Ratifying `[design]` means an accepted RFC's named table never existed, which the erratum records rather than repairs.

**Revisit if:** a consumer needs a silent default with no confirmation step, or `semantic-surface-resolution.v1` changes the tiers it returns.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** a change that adds or alters a layout-config resolution path states its six § 4 steps, and introduces no fallback between configuration and confirmation. A new consumer needs no amendment to this record (D5); one that adds a silent default contradicts D2 and D3.
- **Owner:** eugenelim.

## Alternatives considered

- **RFC-0040's pack-default tail governs.** Rejected against *shipped conformance* and *cost to standing evidence*: no consumer implements it, and adopting it would require reversing `architect-design/SKILL.md:312-317` (conformant under two Shipped specs), contradicting the six Shipped `m2-*` elicitation criteria, and editing `desk-research`.
- **Keep both, scoped by pack.** Rejected against *shipped conformance*: two orders for one file is the defect this record closes, and a per-pack split makes the next consumer choose rather than inherit.
- **Ratify § 4 but also restore RFC-0050 D6's designed-default tier in experience-design.** Rejected against *cost to standing evidence*: it reintroduces the silent default those skills deliberately removed, and D2 already explains the manifest default as an install-time seed, so no tier is missing.
- **Rename the `[design]` table to `[experience]` per RFC-0050 D6.** Rejected against *adopter stability*: the name was never shipped, two packs read `[design]`, and renaming breaks every adopter's existing section with no migration.

## References

- `docs/architecture/agentbundle.md` § 7.2 — how the file is created and which tier a session may read.
- `docs/rfc/0096-portable-delivery-artifact-lifecycle.md:99-105` — the ratified order.
- `docs/rfc/0040-consolidated-pack-layout-config.md:193-198` — the declined tail.
- `docs/rfc/0050-the-experience-pack.md` § Errata — records D6's supersession by this record.
