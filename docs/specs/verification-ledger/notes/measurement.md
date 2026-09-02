# How the defect class was counted

Pre-approval research for `spec.md`'s Measurement assumption. This is not the
delivery's verification ledger — it records the corpus measurement that
established the defect class, taken before the spec was approved. Execution
observations belong in `verification-ledger.md`.

The commit-tree baseline is `98df5599c`, `packs/core` 2.22.0. Instrument A
ran against that 376-plan tree. Instrument B ran later against the working tree
at that baseline plus this delivery's then-uncommitted pair, whose plan raised
its population to 377; this distinction is material to its raw result.

## What was counted

A plan carries the defect when it states an obligation whose discharge requires
a **post-approval write to a hash-pinned artifact** — `plan.md`
(`approved_plan_hash`, and `plan_hash` after `schedule`) or `spec.md`
(`approved_spec_hash`). Both are compared through
`sha256_canonical_contract`, so only the status token and progress-checkbox
brackets survive normalisation.

The adjudicated denominator is **376** `plan.md` files in the commit tree before
this spec directory existed. The then-working tree carried 377 plans because it
also contained this delivery's uncommitted plan; the final numerator and
denominator both exclude that plan.

## Two instruments were required

Neither instrument alone produced a defensible number.

### Instrument A — flat phrase grep

```
grep -rlniE "observed [a-z]+ is recorded here|recorded in (this|the) (plan|table)|record(ed)? (the )?(observed|measured|result|verdict|red|digest)[^.]{0,40}(here|in this (table|row|plan))|its output recorded here|verdict table records" docs/specs/*/plan.md
```

Returned 5 plans. **It missed two real sites** because they name the artifact by
filename rather than by "here" or "this plan":

- `stale-reference-corrections/plan.md:67` — "the evidence recorded in `spec.md`"
- `self-hosting/plan.md:457` — a second site in a plan A already matched at :478

### Instrument B — structural `Done when:` parser

Parsed each `Done when:` statement, then tested whether its destination is a
frozen artifact, with a filter for the negated sense. It ran over 377
working-tree plans and returned 8. **It produced two false positives** its
negation filter failed to exclude:

- `status-projection-and-context-exclusion/plan.md:638` — states the values
  "live there and are **not repeated here**", the opposite sense
- `docs/specs/verification-ledger/plan.md:74` — this delivery's own T1, which
  names the ledger as the destination *instead of* the frozen artifacts

Instrument B also sees only `Done when:` statements, so it misses
`cooling-scope-closure/plan.md:136`, where the obligation is stated in a
mutation-table row rather than a task's Done-when.

### Adjudicated union

| Plan | Site(s) | Destination the obligation names | Class |
| --- | --- | --- | --- |
| `cooling-scope-closure` | 136 (table row), 445 (Done when) | its own mutation table | mutation table |
| `self-hosting` | 457, 478 | plan `## Changelog` **and** `spec.md` AC artifact field | both frozen artifacts |
| `stale-reference-corrections` | 67 | `spec.md` | spec.md |
| `claude-plugins-manifest-correctness` | 208 | plan `## Changelog` | plan Changelog |
| `local-gate-ci-parity` | 275 | plan `## Changelog` and the PR description | plan Changelog |
| `workspace-backlog-reconciliation` | 42 | "its output recorded here" | command output |

**6 of 376 pre-existing plans, 7 task-level sites.** This excludes this
delivery's plan from both numerator and denominator.

## What the distribution changes

The classes overlap; they do not partition the union. **1 of 6** names a
mutation table (`cooling-scope-closure`), **3 of 6** name the plan's
`## Changelog` (`self-hosting`, `claude-plugins-manifest-correctness`,
`local-gate-ci-parity`), **2 of 6** name `spec.md` or its acceptance-criterion
artifact field (`self-hosting`, `stale-reference-corrections`), and **1 of 6**
names “recorded here” (`workspace-backlog-reconciliation`). `self-hosting`
belongs to both the Changelog and `spec.md` classes.

Two consequences for the contract:

1. The rule covers **both** frozen artifacts, not `plan.md` alone. A plan-only
   rule leaves 1 of 6 wholly unaddressed (`stale-reference-corrections`) and 1
   of 6 partially addressed (`self-hosting`). The guard's independent
   `approved_spec_hash` comparison makes the extension correct regardless of
   corpus frequency.
2. The template's `## Changelog` instruction is phase-scoped to `Drafting`,
   because it is the single most common source of the defect.

## False-positive warning for a later reader

Re-running instrument A gives a raw hit list that needs inspection, not a
count. "Recorded" appears in the opposite, non-obligation sense in at least
`direct-skill-repository-installation/plan.md:86` ("rather than from a figure
recorded here") and in this delivery's own plan. A count taken from either
instrument without adjudication is wrong in both directions.
