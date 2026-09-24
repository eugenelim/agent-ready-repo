# ADR-0126: Integration packs carry standalone value, and coupling lives in named bridge skills

- **Status:** Accepted
- **Date:** 2026-09-24
- **Areas:** packaging, contracts
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0019 (one-way projection for repo-origin work); ADR-0077 (the two authority modes a bridge skill operates under); ADR-0125 (what projects, for the bridge half only)

## Decision summary

- **Decision:** A pack that integrates an external delivery system delivers usable value with none of this repository's machinery installed, and every coupling to that machinery lives in a separate, named bridge skill.
- **Because:** A team evaluating the Jira pack for flow metrics should not have to adopt an intent model to get them, and a pack that cannot be tried on its own cannot be adopted incrementally.
- **Applies to:** every pack whose subject is an external system — today `atlassian`, `linear`, `github` — and to any skill added to one.
- **Tradeoff accepted:** a capability that is natural to express once must sometimes be split across two skills, and two of the three current packs do not yet satisfy this.
- **Revisit if:** a provider's API makes a useful standalone read impossible without the intake route, or the split forces a skill pair whose halves nobody uses separately.

## Context

The repository publishes integration packs alongside an intent-driven delivery
system. Nothing records whether an integration pack may depend on that system,
and the three shipped packs answer the question differently.

Measured on 2026-09-24 across `packs/{atlassian,linear,github}/.apm/skills/`,
counting a skill as coupled when its `SKILL.md` references `docs/product/`, an
intent tree, `workspace.toml`, canonical intent, a delivery brief, or the
`work-intake` route:

| Pack | Skills | Coupled | Standalone |
| --- | --- | --- | --- |
| `atlassian` | 13 | 4 | 9 |
| `linear` | 3 | 3 | 0 |
| `github` | 2 | 2 | 0 |

In `atlassian` the boundary is clean: all four coupled skills are
`jira-brief-intake`, `jira-align-brief-intake`, `jira-refresh` and
`jira-align-refresh`, and the nine that remain — including `flow-metrics`,
`jira-team-status` and `jira-story-triage` — work for a team that has adopted
nothing else. A Jira user gets flow metrics and a backlog status view on
install.

`github` has no standalone skill at all: both its skills are bridges. `linear`
shows a third shape — its `linear` skill mixes a standalone read half with a
write half routed through `work-intake`, so the boundary runs *through* a
skill rather than between skills.

The immediate occasion is a set of ten delivery specs drafted for CAP-0004.
Every one of them assumes the intent system is present, and three —
`delivery-state-observation`, `flow-distribution-sample-honest` and
`delivery-forecast-with-uncertainty` — scope their subject to "intent-backed
work", which yields nothing for an adopter who has not adopted. The underlying
readings work over any Jira scope; the restriction is in the contract, not the
capability.

This matters for CAP-0004 specifically, whose premise is coexistence with a
delivery system a team already runs. A pack that requires the intent model
before it returns anything contradicts that premise at the point of first
contact.

## Decision

An integration pack delivers usable value with none of this repository's
machinery installed.

- **D1:** A pack whose subject is an external system ships at least one skill
  that returns value with no repository artifact present — no intent tree, no
  `docs/product/`, no `workspace.toml`, no `work-intake` route.
- **D2:** Coupling to that machinery lives only in skills the pack declares as
  bridges. A bridge skill is where the intent model, the intake route and the
  brief lifecycle may appear.
- **D3:** No skill mixes a standalone capability with a coupled one. Where a
  provider offers both — a free read and a bridged write — they are separate
  skills, so an adopter can install the boundary rather than reason about it.
- **D4:** A pack declares its bridge skills in `pack.toml`. The declaration is
  what a check reads; the naming convention that produced `-brief-intake` and
  `-refresh` is a convention, not the contract.
- **D5:** This governs packs whose subject is an external system. It does not
  reach a pack whose subject *is* the machinery — `product-engineering` and
  `core` are not integration packs and D1 does not apply to them.

## Decision drivers

- **Incremental adoption.** CAP-0004's whole premise is coexistence with the
  delivery system a team already runs. Value before adoption is what makes
  that testable.
- **Evaluability.** A team assessing a pack installs it and asks what it
  does. A pack that answers "nothing yet" has failed the assessment.
- **A measurable adoption delta.** When the standalone slice exists, what
  adopting the intent system *adds* can be stated against it rather than
  against nothing.
- **Enforceability.** A boundary between skills is checkable; a boundary
  inside a skill is a reading.

## Consequences

- A team can take the Jira pack for flow metrics and a kanban view and decide
  about the intent model separately, which is what CAP-0004 assumes.
- The adoption delta becomes a thing that can be demonstrated: same view,
  outcome sourced from the canonical intent instead of elicited.
- `linear` and `github` do not satisfy D1 today, and `linear` does not satisfy
  D3. This decision creates that debt rather than discovering it; neither pack
  is required to change before its own next slice.
- Some capability is expressed across two skills where one would have read
  more naturally, and an adopter installs both.
- The ten CAP-0004 specs need a standalone slice ahead of them, and the three
  that scope to "intent-backed work" need intent-backing demoted to an
  optional filter.
- **Revisit if:** a provider's API makes a useful standalone read impossible
  without the intake route, or a forced split produces a skill pair whose
  halves nobody uses separately.

## Alternatives considered

- **Leave it to precedent.** Rejected: precedent is realised in one pack of
  three and points three different ways, and the ten specs drafted this week
  would all have broken it without anyone noticing.
- **Permit coupling anywhere and document the dependency.** Rejected: a
  documented dependency still means the pack returns nothing on install, which
  is the outcome CAP-0004's coexistence premise cannot afford.
- **Split every integration pack into a base pack and a bridge pack.**
  Rejected: it doubles catalogue entries, install steps and version surfaces to
  express a boundary that a skill-level rule already expresses, and adopters
  would have to discover the pairing.
- **Require standalone value from every pack.** Rejected as overreach:
  `product-engineering` and `core` exist to be the machinery, and D1 would be
  incoherent there. Hence D5.

## Confirmation

- **Mode:** lint/CI
- **Signal:** for each pack declaring bridge skills in `pack.toml`, no
  non-bridge skill's `SKILL.md` references `docs/product/`, an intent tree,
  `workspace.toml`, canonical intent, a delivery brief, or the `work-intake`
  route; and each such pack ships at least one non-bridge skill. A pack that
  declares no bridge skills and references none of those things passes
  trivially.
- **Owner:** eugenelim

## References

- Backfill in part: D1 and D2 record a boundary `packs/atlassian` has followed
  since it shipped. D3, D4 and D5 are new.
- Measurement behind the Context table: `packs/{atlassian,linear,github}/.apm/skills/*/SKILL.md`, read 2026-09-24.
- [`docs/product/briefs/intent-backed-working-view.md`](../product/briefs/intent-backed-working-view.md) — the delivery brief whose specs occasioned this.
