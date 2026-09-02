# Amendment authority and reason

This note is the stable locator cited by the `contract-amendment` transition's
`--owner-authority-ref` and `--reason-ref`. It records who authorized the
sealed-baseline replacement and the measured evidence that made it necessary.

## Owner approval

The scope owner approved the amendment on 2026-09-01, after reviewing the
proposed delta, the new plan task T9, the transition sequence, and the cost (two
further human gates, a fresh spec-stage review, and a re-seal). Review then
withdrew two of the four proposed criteria; the owner approved the narrowed
delta — AC34 and AC35, with AC31 amended in place — the same day. The
owner separately directed that the entry-class defect be repaired within this
delivery rather than deferred, since the amendment already reopens the seam.

Authority covers reopening the sealed baseline under ADR-0099
(`docs/adr/0099-shaping-review-and-sealed-baseline-replacement.md`), which admits
"a material correction to a sealed spec or plan". It does not authorize editing a
completed task section, overwriting the prior pin, or erasing completed history.

## Reason: the criteria set is blind to entry class

Every closeout fixture behind AC1–AC33 uses a canonical
`docs/specs/<slug>/spec.md` work entry. No criterion names an entry *class*, so
the set is complete against what it enumerates and silent about every other
shape a `work.*` collection accepts. Two successive defects passed all 33 green
criteria in that same blind spot.

The second defect reached `origin/main` in PR #1210, which merged during the
review round. The repair for it on this branch — `fix(core)!: consume
reconciliation's cooled verdict in closeout`, `5463ff3ee` at the time of
writing — added no test: it was verified by a manual probe that was never
committed as a guard. That is the gap AC34 and AC35 close.

### Measured differential

Both trees run their own `workspace-status` against identical fixtures: one
`work.queue` entry, one initiative, one `Cooling` lifecycle record naming
`docs/specs/thing/spec.md`. Instrument validated first — the record must load
(`cooling.due_count == 1`) or the comparison is void.

| Entry class | `origin/main` (`d6b2298a1`) | This branch |
| --- | --- | --- |
| canonical, cooled | `invoke-close-work` | `invoke-close-work` |
| canonical, uncooled | `settle-closeout-blockers` | `settle-closeout-blockers` |
| legacy `spec/<slug>`, cooled | `invoke-close-work` | `invoke-close-work` |
| legacy `spec/<slug>`, uncooled | `settle-closeout-blockers` | `settle-closeout-blockers` |
| bare slug + record | **`invoke-close-work`, `all_specs_shipped=true`** | `settle-closeout-blockers`, `false` |

Four classes agree; the divergence is confined to the bare slug the canonical
layer refuses to model at all (`unsupported_legacy`). On `origin/main` an
initiative whose last queue item is such an entry reports every spec shipped and
is offered closeout, while reconciliation reports the item unrouted.

### Exposure

The defect needs a cooled bare-slug `work.*` entry. This repository has neither
precondition today: `docs/lifecycle/` holds only `README.md` (zero cooling
records), and no `work.*` collection holds a string-form entry. The repair
therefore ships with its guard on the ordinary path rather than as a hotfix.
