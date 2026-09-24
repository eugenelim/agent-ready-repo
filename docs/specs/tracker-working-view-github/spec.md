# Spec: tracker working view github

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0125; ADR-0077; ADR-0019
- **Brief:** brief:intent-backed-working-view
- **Discovery:** none
- **Contract:** none
- **Shape:** integration


> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

<!-- **Durable-spec fill.** This template governs work that needs a durable
behavior contract for one delivery slice. Fill Outcome, What Changes, Agent
Rules, Testing Strategy, and Acceptance Criteria to the depth the durable work
requires, and Assumptions only where something is unresolved. The sibling plan carries the implementation and verification strategy.
Eligible direct-light work does not create this artifact. -->

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
release changelog. `plan.md` holds to the same rule: its `## Changelog` records
approvals, not how the approach evolved. -->

## Outcome

A team running GitHub Issues + Projects sees its canonical intent tree as
GitHub work it can act on, within the depth GitHub's sub-issue hierarchy
allows, and gets shaped intent written back onto issues it already holds.
Success is that the board carries the tree's structure without anyone
rebuilding it by hand.

## What Changes

- GitHub Issues + Projects gains a column in the shared level-to-object profile
  table —
  `packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md`
- `github-refresh`, which already owns every GitHub write, gains the confirmed
  create path — `packs/github/.apm/skills/github-refresh/`
- A GitHub projection renders ADR-0125's range as issues and sub-issues
  carrying a back-reference — `packs/github/`
- The GitHub return leg extends to shaped intent on existing issues —
  `packs/github/.apm/skills/github-refresh/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — the confirmed create path lands in the skill that already owns GitHub writes | `packs/github/.apm/skills/github-refresh/SKILL.md` | this spec | the create action handled there, and `github-brief-intake` still refusing every write verb | no write verb runs without the bounded action set's confirmation |
| Reusable learning | Applicable — the vendor limits are scalars that change at source | `docs/specs/tracker-working-view-github/notes/` | this spec | a dated extract of GitHub's own sub-issue documentation carrying the nesting and per-level maxima | the implementation reads the extract rather than literals |
| Maintainer procedure | Applicable — the GitHub column is authored by the pattern slice and exercised here | `packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md` | pattern slice | the column resolves against a real GitHub render | the render matches every row |
| Release history | Applicable — `github` changes | `packs/github/CHANGELOG.md` | this spec | one entry | the pack leads its own entry |
| Current architecture | Not applicable — the pattern document is the Jira Software slice's output and this slice conforms to it | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Satisfy ADR-0125 D1 and D3: where the tree is deeper than GitHub can nest,
  collapse the surplus rungs onto the carrier the pattern slice selects and
  keep the rollup resolvable.
- Carry the canonical identity on every projected issue and the issue identity
  where a repository reader can find it.
- Treat the back-reference as the projection key.
- Route every mutation through the bounded action set in
  `packs/core/.apm/skills/work-intake/scripts/refresh.py`, under the
  confirmation contract that file already enforces.

### Ask first

- Projecting a rung whose children would exceed GitHub's per-level sub-issue
  maximum, which is a capacity limit rather than a depth one.
- Any use of a write verb outside the bounded action set.

### Never do

- Violate ADR-0019 D5 as ADR-0077 D6-D12 refine it, by letting anything read
  off the tracker acquire authority over canonical intent.
- Violate ADR-0125 D4 by projecting an agent-internal unit as a managed item,
  or D4a by projecting a same-repository delivery brief.
- Violate ADR-0125 D3 by truncating a rung GitHub cannot nest. Depth is a
  collapse case, never a refusal.
- Violate CAP-0004's no-new-runtime guardrail.
- Re-decide a variation point the Jira Software slice's pattern already settles.
- Add a write verb to `github-brief-intake`. That skill reads; `github-refresh`
  owns every GitHub write.
- Give a projected issue a second parent.

## Testing Strategy

- **Vendor limits: goal-based check.** The nesting depth and per-level
  sub-issue maximum are read from a recorded extract of GitHub's own
  documentation held under `notes/`, with its retrieval date, and the
  implementation reads those values rather than literals. A limit that has
  moved at source shows as a stale extract, not as a silently wrong contract.
- **Collapse behaviour: TDD.** A tree deeper than GitHub can nest collapses
  onto the pattern's carrier; the surplus rungs are asserted present, not
  absent.
- **Fan-out refusal: TDD.** Exceeding the per-level maximum is a capacity
  limit with a definite refusal.
- **Projection mapping and idempotency: TDD**, against fixtures, reusing the
  pattern slice's reference-tree shape.
- **The write path: goal-based, manual QA.** No test writes to a live GitHub; a
  recorded confirmation transcript is the evidence.

## Acceptance Criteria

- [ ] Projecting the reference tree onto an empty repository yields one GitHub
      object for every rung in ADR-0125's range and none for any rung outside
      it. A run yielding zero objects fails.
- [ ] The rollup from the floor rung to the top rung of that projection
      resolves through each carrier the collapse selected.
- [ ] A projected GitHub issue names the canonical artifact it came from.
- [ ] A repository reader can determine which GitHub issue a rung was
      projected to, from the repository alone.
- [ ] A tree deeper than GitHub's nesting maximum collapses its surplus rungs
      onto the pattern's carrier, and every surplus rung is still reachable in
      the rollup.
- [ ] The nesting maximum and the per-level sub-issue maximum are read from the
      recorded vendor extract under `notes/`, not from literals in the
      implementation.
- [ ] A rung whose children exceed the per-level maximum is refused with the
      limit named.
- [ ] No projected issue has more than one parent.
- [ ] Projecting the reference tree onto a repository that already holds the
      team's issues yields no second managed object for any rung an existing
      issue already carries the back-reference for.
- [ ] Where a rung's counterpart exists without a back-reference, the
      projection refuses that rung and names it, before any mutation.
- [ ] Projecting an unchanged tree a second time changes no issue count.
- [ ] No write verb executes without the bounded action set's single-use,
      session-fresh confirmation.
- [ ] The GitHub profile declares the create capability, and before that
      declaration lands the action refuses even though it is present in the
      shared action set.
- [ ] Text placed in a GitHub issue title or body cannot select the action,
      the target, the destination, a field, the credential or the content of a
      confirmation.
- [ ] A confirmation presented for a write shows the exact per-item payload and
      the protected-field set that write will not touch.
- [ ] One fresh confirmation creates exactly one intended issue, and
      re-presenting it creates nothing.
- [ ] `github-brief-intake` executes no write verb.
- [ ] Repository scope is derived from the canonical artifact's owning
      repository and the projection target's, not from a hand-maintained list.
- [ ] A delivery brief whose work stays in the canonical artifact's own
      repository produces no GitHub object.
- [ ] A delivery brief whose work crosses a repository boundary produces
      exactly one managed GitHub object.
- [ ] An agent-internal unit produces no GitHub object that is scheduled,
      assigned or counted.
- [ ] Projection runs only when invoked and leaves no resident process.

## Follow-ons

none

## Scope decision

**Projection and the return leg ship as one slice.** They have separate success
conditions and could ship apart. They are paired here because the parent brief
records the pairing as the lifecycle owner's cut, confirmed 2026-09-24, and
states that whether it is one slice or two is not settled by that brief. This
spec inherits the cut and does not re-test it. The ground is the owner's
decision, not an argued indivisibility.

## Assumptions

- Whether GitHub Projects v2 board fields are needed for the rollup to be
  readable, or whether sub-issue nesting alone carries it. Community reports
  say grouping by parent issue duplicates parent rows or drops parentless
  issues; whether that degrades the rollup enough to matter is observable only
  against a real board, and an adopter settles it.
