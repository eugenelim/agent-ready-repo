# Autonomous product-team operating model

- **Slug:** `autonomous-product-team-operating-model` <!-- canonical identity; independent of the filename ordinal -->
- **Kind:** opportunity <!-- chain rung: the need this strategy addresses on the opportunity-solution tree; orthogonal to Level -->
- **Status:** Draft
- **Level:** product-strategy
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** ai-native-ecosystem — [AI-native ecosystem](VISION-0001-ai-native-ecosystem.md)

## Outcome

- **Steerable input:** The share of the path from outcome to deploy-ready change that non-engineering layers — product, design, experience, research — can carry without handing off to engineering to be translated.
- **Lagging outcome:** Autonomy extends past engineering. A product, design or research layer acts within the same operating model, and its output is directly actionable by the layer below rather than needing an engineer to interpret it.
- **Guardrail:** Judgement is decomposed and equipped, not automated away. Gates stay risk-calibrated rather than uniform, so a low-risk change is not held to a high-risk bar and a high-risk one is not waved through.

## Opportunity

- **Functional job:** Take a product outcome through journey, screen, service and contract to something buildable, inside one operating model rather than across a handoff.
- **Emotional job:** Contribute at your own altitude without becoming a bottleneck or a translator for someone else's.
- **Social job:** Show that product and design work is first-class in an agentic delivery model rather than upstream commentary on it.
- **Struggling moment:** The catalogue can build downstream of a spec but cannot act as a product team upstream of one. Nothing turns an outcome into a journey, a journey into a screen inventory, or a screen into its backing service — so every non-engineering layer's output stops at prose and waits for an engineer.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this strategy's outcome.

## Unresolved questions

- Whether non-engineering judgement can be decomposed and equipped rather than only exercised by an experienced practitioner.
- Whether a risk-calibrated gate ladder is applied honestly rather than collapsing to its lowest tier under delivery pressure.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Boundary

Includes the connective experience layer from outcome through journey, screen and service to contract; the two-regime principle; the judgement-decomposition-to-equipping map; and the risk-calibrated gate ladder **as doctrine** — what rigour a change attracts and why. The loops that execute that doctrine belong to [Platform Core](STRAT-0002-platform-core.md).

Excludes the engineering loops themselves ([Platform Core](STRAT-0002-platform-core.md)), the model of work ([Graph-powered SDLC](STRAT-0001-graph-powered-sdlc.md)), and distribution ([Trustworthy organisation-owned catalogues](STRAT-0004-trustworthy-org-owned-catalogues.md)). It decides a model and a roadmap; each artifact is built by a named child effort rather than here.

## Assumptions

- Non-engineering judgement can be decomposed and equipped rather than only exercised by an expert. **Untested**, and it is this strategy's load-bearing bet.
- A risk-calibrated gate ladder is applied honestly rather than collapsing to the lowest tier under delivery pressure. **Untested.**
- **Knowledge surface:** in-repo doc set. Extracted 2026-09-18 from [RFC-0048](../../rfc/0048-autonomous-product-team-operating-model.md), Accepted, whose four acceptance blockers were discharged 2026-06-30.

**Not de-risked.** Extracted to complete the vision's decomposition, not shaped fresh. Re-enter `frame-intent` → `de-risk-intent` before treating it as a tested bet.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
