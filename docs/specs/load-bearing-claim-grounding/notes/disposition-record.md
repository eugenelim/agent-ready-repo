# Resolve-vs-surface disposition record: load-bearing-claim-grounding

Opened at PLAN, closed at DECIDE. Every open item is either resolved with its
referent or surfaced with a reason.

## Surfaced to the owner — four, each because it was the owner's call

| # | Item | Reason surfaced | Outcome |
| --- | --- | --- | --- |
| S1 | Whether the two already-owned evidence shapes ship as rules or as routing references | Value conflict: it changes what ships, and the intake pre-authorised narrowing without choosing the form | Owner chose routing references only, 2026-09-17 |
| S2 | Whether to extend the sample after round 4 cut both surviving demands | The replay's kill condition had effectively fired for the evidence-selection half; continuing or killing is an owner decision | Owner directed extending the sample, which then cut the last demand |
| S3 | Whether to approve the recut contract and proceed to implementation | Human approval gate; not resolvable by any referent | Owner approved spec and plan, 2026-09-17 |
| S4 | `grounding-probe-extensions` adjacency | The owner asked directly whether that intent covers this work | Answered: adjacent, not the same; two of its recorded decisions now constrain this slice |

## Resolved with a referent — every other open item

| Item | Referent |
| --- | --- |
| Does this need an RFC? | `CONTRIBUTING.md:33` — none of its five conditions applies |
| Which surface owns the rule | The assumptions step's own defective sentence; `work-loop`'s domain-grounding hook is scoped to domain claims |
| Whether step 5a is in scope | `docs/product/briefs/agent-authoring-input-quality.md` § "Slice relationships" assigns it to slice A4 |
| Whether any evidence shape is earned | [`replay.md`](replay.md), seven deliveries, each cut recorded with the evidence against it |
| Whether the discriminator was testable | No `plan.md` in the sample records an owner-approval line; withdrawn |
| Release surface size | No `"core"` entry in `.claude-plugin/marketplace.json` — three files |
| Whether projection parity needs a control | `tools/repo/build_gate_chain.py` runs `catalogue self-host --check` inside `make build-check` |
| Whether an eval is coverage | `--check` defaults to `activation`; `pack-evals.yml` passes no mode — it is documentation |
| Whether a behavioural gate is possible | Rubric class 6 sends a judgement over authored prose to advisory; `grounding-probe-extensions` refused a grader after three calibrations |

## Review findings — all resolved, none deferred

Nine adversarial rounds (10, 8, 5, 7, 4, 1, 2, 1, 0) and a quality pass (5),
**41 findings, every one sustained, none refuted, none deferred.** Two review
rounds also ran pre-approval on the contract (16 and 7).

Of the quality pass's five: two repaired, one control kept with an actionable
failure message, one accepted as proportionate with its reason, one bounded to
`guidance-activation-measurement.md` with that owner named. No Nit is carried
unresolved.

## Named skip

`experience-reviewer` — non-mandatory, and its confirm-before-reviewing gate
requires rendered output plus a grounded aesthetic reference. This diff's
adopter-visible surfaces are one paragraph in a how-to guide and one changelog
entry, both prose with no rendered artifact and no aesthetic direction to ground
against. Skipped by name rather than silently, and the two surfaces were instead
read against the contract by the adversarial rounds, which found and fixed a
second-home violation in each.
