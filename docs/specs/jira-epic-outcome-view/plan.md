# Plan: jira epic outcome view

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/atlassian/.apm/skills/jira-team-status/SKILL.md`
  (readiness, blocked, in-progress, unassigned, stale and dependency risk,
  with its own staleness thresholds); `packs/atlassian/.apm/skills/flow-metrics/SKILL.md`
  (nine metrics at p50, p75 and p90 from changelogs, Jira-only by pack);
  `packs/atlassian/.apm/skills/jira/SKILL.md` (the read client);
  `packs/atlassian/pack.toml` (where ADR-0126 D4's bridge declaration lands).
  Named deviation: no skill in this pack composes two other skills today, so
  the composition boundary has no precedent here.


> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling

## Approach

Almost nothing is new. `jira-team-status` and `flow-metrics` already answer the
delivery half for a Jira scope, and both are standalone — neither references
any of this repository's machinery. This slice groups their output by Epic and
puts an outcome next to it.

The one real decision is where an elicited outcome lives between one run and
the next, because no repository artifact is permitted and no write to Jira is
either. **The outcome lives in Jira, written by the team.** The view reads it
from a documented location; where it is absent, the view says so and hands the
team paste-ready text. That keeps the skill read-only, keeps the outcome
beside the work it describes, and means the second run is better than the
first without anything of ours persisting. The alternative — re-eliciting
every run — was rejected because a view that forgets is a view nobody opens
twice, which is the failure the parent's success signal names directly.

The riskiest part is the absent-outcome path, and it is risky because it is
the tempting one to drop: an Epic with no outcome contributes nothing to a
view trying to look complete. Dropping it reproduces the selection effect the
capability's research measured, so it is asserted by removal rather than by
presence.

## Constraints

- **ADR-0126 D1** obliges this skill to return value with no repository
  artifact present; **D2** confines coupling to declared bridge skills and
  this is not one; **D3** forbids mixing a standalone capability with a
  coupled one; **D4** requires the pack to declare its bridges in `pack.toml`.
- **ADR-0077** governs tracker-origin reading. Nothing read here acquires
  authority over anything.
- The parent intent's guardrails: read-only, adoption stays optional, and the
  outcome is never authored by this feature.
- `flow-metrics` stays Jira-only and in its own pack. This slice composes it
  rather than moving or generalising it.

## Construction tests

- A fixture Jira scope with Epics carrying outcomes and Epics carrying none.
- A removal assertion: taking any Epic out of the rendered view fails.
- A verbatim assertion comparing rendered outcome text to the source.
- A filesystem hash before and after, with `.context/flow-metrics/cache/`
  pre-populated, asserted byte-identical.
- A run from a non-repository working directory with adopter-repository paths
  denied, asserted to return a correct non-empty answer.
- A coupling grep over the skill's sources, plus a walk of its dependency and
  invocation graph for any path reaching a pack-declared bridge, with a
  bridge-calling fixture that must fail.
- A composition assertion: the figures match what the two shipping skills
  return for the same scope and window.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Composed delivery reading grouped by Epic | T1 | figures match the shipping skills |
| Outcome read and absent-outcome rendering | T2 | removal assertion fails for every Epic |
| Read-only and zero-coupling guarantees | T3 | no write verb, no file, no machinery reference |
| Bridge declaration in `pack.toml` | T3 | this skill absent from the list |
| `atlassian` changelog entry and the user-facing promise | T3 | one entry; what the view answers drafted |

## Design (LLD)

### Design decisions

- **The outcome lives in Jira, written by the team.** No repository artifact
  is permitted and this slice writes nothing, so those are the only two
  candidates. Storing it in Jira keeps the outcome beside the work, survives
  between runs, and costs this skill no write authority.
- **Paste-ready text rather than a write.** Handing the team the exact string
  and its location gets the outcome recorded without this skill acquiring the
  authority to record it, which is the parent's guardrail.
- **Compose, do not recompute.** Re-deriving cycle time here would put a
  second definition of it in the same pack, and the two would drift with
  nothing comparing them.
- **The composed `flow-metrics` call bypasses its cache.** It writes
  `.context/flow-metrics/cache/<cache-key>.jsonl` by default, so composing it
  unchanged would make a read-only view write to disk on its first run and
  rewrite on every later one.

### Data & schema

Input is a Jira scope. Per Epic: the delivery reading from the two shipping
skills, plus the outcome text read from the documented location. Output
carries both, the sample size behind any percentile, and the moment each
reading was taken.

### Interfaces & contracts

No new interface. The two shipping skills are invoked as they stand.

### Component / module decomposition

One new skill in `packs/atlassian/.apm/skills/`, plus the `pack.toml` bridge
declaration.

### State & control flow

Computed on invocation. No cache, no resident state, nothing written.

### Behavior & rules

An Epic with no outcome renders with an explicit nothing and its paste-ready
text. An Epic whose outcome location holds something unparseable renders the
raw text rather than discarding it, because discarding is indistinguishable
from absent.

### Failure, edge cases & resilience

A Jira error is surfaced rather than rendered as an empty scope, because "no
Epics" and "could not reach Jira" are different facts. A scope with zero
completed items still renders the state half, which needs no sample.

### Quality attributes (NFRs)

Read-only is the pass/fail bar: no write verb, no file. The sample thresholds
`flow-metrics` already applies govern every percentile.

### Dependencies & integration

A Jira credential through the broker, already this pack's requirement. No new
dependency, and explicitly nothing from this repository's machinery.

## Tasks

### T1: the delivery reading is composed and grouped by Epic

**Depends on:** none

**Tests:**
- Figures match what `jira-team-status` and `flow-metrics` return for the same
  scope and window. Verifies *the state and flow figures match*.
- Every rendered reading states its moment, and a percentile appears only
  where its sample supports it. Verifies those two criteria.

**Approach:**
- The two skills are invoked as they stand. Recomputing would create a second
  definition of cycle time inside one pack.

**Done when:** the composition assertion holds against the fixture scope.

**Touches:** packs/atlassian/.apm/skills/**

### T2: every Epic appears, and one without an outcome says so

**Depends on:** T1

**Tests:**
- An Epic's recorded outcome is reproduced verbatim. Verifies *reproduced
  verbatim from the documented Jira location*.
- The expected Epic set is derived from the completed Jira result and the
  rendered set equals it exactly; each member is a failing removal control.
  Verifies the three scope-completeness criteria.
- Every outcome-less Epic in a fixture holding several renders both the
  explicit nothing and the paste-ready text. Verifies those three criteria.
- A fixture where the feature would supply outcome substance fails. Verifies
  *paste-ready text contains only a fixed, non-substantive scaffold*.
- No score, grade or judgement appears. Verifies *renders no score, grade or
  judgement*.

**Approach:**
- Completeness is asserted by removal. An omitted Epic raises no error
  anywhere, so a presence assertion passes while the set silently shrinks.

**Done when:** the removal fixture fails for every Epic in scope.

**Touches:** packs/atlassian/.apm/skills/**

### T3: the skill writes nothing and couples to nothing

**Depends on:** T1

**Tests:**
- The filesystem is byte-identical across a run with a populated cache
  seeded, and the composed `flow-metrics` call bypasses its cache. Verifies
  *leaves the filesystem byte-identical* and *bypasses its on-disk cache*.
- No Jira write verb is issued. Verifies *issues no Jira write verb*.
- The view returns its answer with no repository artifact present. Verifies
  *returns its answer with no repository artifact present*.
- The skill's sources contain no machinery reference, and `pack.toml` declares
  the pack's bridges without listing this skill. Verifies those two criteria.

**Approach:**
- The bridge declaration lands here because ADR-0126 D4 makes it the thing a
  conformance check reads, and this is the pack's first skill obliged by it.

**Done when:** the read-only and coupling assertions are green, `pack.toml`
declares its bridges, `packs/atlassian/CHANGELOG.md` leads an entry, and what
the view answers is drafted on the user-facing surface.

**Touches:** packs/atlassian/.apm/skills/**, packs/atlassian/pack.toml, packs/atlassian/CHANGELOG.md

## Rollout

Nothing existing changes behaviour: the two composed skills are invoked
unmodified, and the `pack.toml` addition is a declaration. The slice is
revertible by deleting one skill directory and one declaration.

## Risks

- **The absent-outcome row gets dropped as noise.** Mitigated by asserting
  removal rather than presence.
- **A team never records an outcome.** Then the view degrades to the delivery
  half, which is what already ships — a weak product rather than a broken one.
  This is the parent's `to-validate` hook, not something this plan settles.
- **The composition drifts from its sources.** Mitigated by asserting the
  figures match the two skills rather than snapshotting expected numbers.

## Changelog

- 2026-09-24 — plan drafted.
