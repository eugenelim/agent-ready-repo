# Amendment: authority, reason, and withdrawal

This note is the stable locator cited by the `contract-amendment` transition's
`--owner-authority-ref` (`#owner-approval`) and `--reason-ref`
(`#reason-the-criteria-set-is-blind-to-entry-class`). Those anchors are pinned in
engine state and must keep resolving, so this note is retained even though the
amendment it authorized was withdrawn. It records what was attempted, what was
measured, and what shipped instead.

## Owner approval

The scope owner authorized reopening the sealed baseline on 2026-09-01 under
ADR-0099 (`docs/adr/0099-shaping-review-and-sealed-baseline-replacement.md`),
which admits "a material correction to a sealed spec or plan". The owner also
directed that the entry-class defect found after PR #1210 be repaired within this
delivery rather than deferred.

**That directive was satisfied by code, not by contract.** The repair is on this
branch and is what ships. The owner subsequently directed, on 2026-09-02, that
scope be cut to what is certain: the contract amendment is withdrawn, and the
spec and plan return byte-identical to the pair already approved and merged in
PR #1210. Every criterion the amendment proposed, and every finding that survived
adjudication, is recorded in [`review-findings.md`](review-findings.md) instead of
being contracted, and registered canonically in `[backlog].open`.

Authority never extended to editing a completed task section, overwriting the
prior pin, or erasing completed history, and none of those occurred:
`validate_completed_task_sections` reports all seven T1-T7 pins matching.

## Reason: the criteria set is blind to entry class

Every closeout fixture behind AC1-AC33 uses a canonical
`docs/specs/<slug>/spec.md` work entry. No criterion names an entry *class*, so
the set is complete against what it enumerates and silent about every other shape
a `work.*` collection accepts. Two successive defects passed all 33 green
criteria in that same blind spot.

The second reached `origin/main` in PR #1210, which merged during the review
round. The repair for it on this branch — `fix(core)!: consume reconciliation's
cooled verdict in closeout` — added no test: it was verified by the manual probe
below, which was never committed as a guard. Closing that gap by contract was
attempted over three review rounds and abandoned; see § Withdrawal.

### Measured differential

Both trees run their own `workspace-status` against identical fixtures: one
`work.queue` entry, one initiative, one `Cooling` lifecycle record naming
`docs/specs/thing/spec.md`. Instrument validated first — the record must load
(`cooling.due_count == 1`) or the comparison is void. Two earlier attempts at
this probe were void for exactly that reason.

| Entry class | `origin/main` (`d6b2298a1`) | This branch |
| --- | --- | --- |
| canonical, cooled | `invoke-close-work` | `invoke-close-work` |
| canonical, uncooled | `settle-closeout-blockers` | `settle-closeout-blockers` |
| legacy `spec/<slug>`, cooled | `invoke-close-work` | `invoke-close-work` |
| legacy `spec/<slug>`, uncooled | `settle-closeout-blockers` | `settle-closeout-blockers` |
| bare slug + record | **`invoke-close-work`, `all_specs_shipped=true`** | `settle-closeout-blockers`, `false` |

Five rows, not six: the bare-slug class was measured only in its cooled arm, so
its divergence claim rests on an unpaired row. Of the two classes measured in
both arms, both agree across the trees; the divergence is confined to the bare
slug the canonical layer refuses to model at all (`unsupported_legacy`). On
`origin/main` an initiative whose last queue item is such an entry reports every
spec shipped and is offered closeout, while reconciliation reports it unrouted.

A fourth class was found by review and is not measured above: a canonical entry
of a non-spec `kind` whose `path` collides with the stored form of a legacy
entry. Because `parse_workspace_entry` shape-constrains `path` only for
`kind = "spec"` and `kind = "brief"`, and the closeout seam transports its
verdict as a raw path string rather than entry identity, the cooled legacy entry
drags the uncooled one out of the closeout count. Both reviewers measured it with
both controls.

### Exposure

The shipped repair addresses a defect needing a cooled bare-slug `work.*` entry.
This repository has neither precondition today: `docs/lifecycle/` holds only
`README.md` (zero cooling records), and no `work.*` collection holds a
string-form entry (0 of 125). The fourth class shares both and adds a third —
two `work.*` entries of one initiative sharing a raw path string, of which this
repository has none. None of these grants privilege: anyone who can add a
colliding entry can already delete the entry it would hide.

## Withdrawal

The amendment proposed four criteria across three rounds. Both reviewers
sustained findings against every round, and the counts did not fall:

| round | reviewer-introduced by this work |
| --- | --- |
| 1 (`55305a49c`) | 6 blockers, 5 majors — all attributed to the amendment |
| 2 (`5153a017f`) | 13 findings, 7 major |
| 3 (`277042615`) | 14 findings across both lenses, 3 blockers |

Two withdrawals were correct on their merits and are recorded so the reasoning is
not re-derived. **AC36** ("closeout's cooled verdict is reconciliation's") had no
obtainable oracle: the canonical layer publishes the *complement* of a cooled
membership set — `legacy_memberships` and `evaluations` are filtered to
non-cooled, and `cooled` is a set of paths — so every route was a tautology or was
falsified by an `unsupported_legacy` entry, which appears in no membership list
yet must survive. **AC37** stated a second predicate over the artifact AC31
already governs.

The decisive round-3 finding is finding 1 of
[`review-findings.md`](review-findings.md), and it is an authoring defect rather
than a missing work-loop capability — the skill already forbids editing
`plan.md` in-flight: the mutation table instructs that each observed red
is recorded in `plan.md`, but `plan.md` is hash-frozen once `schedule` persists
it, so that edit fails `schedule check-current`. Zero of the twenty mutation rows
record an observed red, and T6 — pinned as completed and merged — records none in
its commit either. The obligation was never dischargeable as written.
