# Plan: tracker working view github

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/github/.apm/skills/github-refresh/SKILL.md` (the shipped
  confirmed write-back, transported by `gh issue comment`, `gh issue edit
  --add-label` and `gh issue close`);
  `packs/github/.apm/skills/github-brief-intake/SKILL.md` (the read path and
  the write refusal this replaces);
  `docs/specs/tracker-working-view-jira-software/` (the pattern). Named
  deviation: GitHub's limits are hard numbers rather than degradation
  behaviour: depth is a collapse case under ADR-0127 D3, while the per-level
  sub-issue maximum is a capacity limit and refuses.


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

The pattern slice has already added the GitHub column to the profile table and
the create action to the bounded set, so this slice is transport and limits.
The confirmed create path lands in `github-refresh`, which already owns every
GitHub write. `github-brief-intake` keeps its refusal untouched, so no trust
boundary moves into a skill whose job is reading.

The riskiest part is depth. GitHub's nesting maximum is a hard vendor number,
but ADR-0127 D3 says rungs above the floor collapse and are never truncated —
so a tree deeper than GitHub can nest must land its surplus rungs on the
carrier the pattern slice selects, and every one of them must stay reachable in
the rollup. A silent flatten is indistinguishable from a correct projection at
the point of reading, which is the parallel-hierarchy failure this feature
exists to remove, so the fixture asserts the surplus rungs are present rather
than asserting no error occurred. The per-level sub-issue maximum is different:
no carrier absorbs it, so it refuses.

## Constraints

- **ADR-0127** D1 through D4a fix what projects and how far; D3 and D5 are
  non-waivable on every delivery system.
- **ADR-0019 D5**, as **ADR-0077 D6-D12** refine it, keeps this one-way for
  repo-origin work.
- **ADR-0033 D2** makes `Level` an open set, so an unmapped rung is named
  rather than derived.
- **CAP-0004's guardrail** forbids a daemon, control plane, database or
  scheduler.
- The pattern the Jira Software slice sets is an input, not a subject. A
  variation point it settles is not reopened here.
- This pack stays independently installable and depends on no other provider
  pack.

## Construction tests

- A depth fixture at the nesting maximum and one rung beyond it: both project,
  and the second asserts its surplus rung present on the pattern's carrier and
  reachable in the rollup.
- A fan-out fixture at the per-level maximum and one child beyond it: the
  first projects, the second refuses with the limit named.
- A projection fixture pair driving the mapping, reusing the pattern slice's
  fixture shape so the two stay comparable.
- An idempotency fixture: same tree twice, then one rung renamed.
- A single-parent assertion over the rendered output.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Confirmed create path in the write-owning skill | T1 | no write verb runs unconfirmed |
| Dated vendor-limit extract | T2 | no maximum appears as a literal |
| Projection and collapse beyond GitHub's depth | T3 | surplus rungs present in the rollup |
| Duplicate and collision behaviour | T4 | populated-repository fixture creates nothing |
| Derived repository scope | T4a | both sides of the brief rule exercised |
| Return leg on existing issues | T5 | recorded confirmation transcript |
| `github` changelog entry | T5 | the pack leads its own entry |

## Design (LLD)

### Design decisions

- **The write owner does not move.** `github-refresh` already holds every
  GitHub write and its action handlers; the create belongs there.
  `github-brief-intake` keeps its refusal, so a reader asking whether the read
  path can write still finds the same answer.
- **Depth collapses, fan-out refuses.** ADR-0127 D3 makes a rung GitHub cannot
  nest a collapse case, not a truncation, so it lands on the pattern's carrier.
  A rung whose children exceed the per-level maximum has no carrier to collapse
  onto, so it refuses with the limit named. The two are different failures and
  the contract treats them differently.

### Data & schema

The profile table's GitHub column is the schema. The projection payload carries
the canonical identity, the rung's `Level`, and the target object type resolved
from that row.

### Interfaces & contracts

No new interface. The create action and its confirmation binding ship with the
pattern slice; this slice supplies GitHub's transport for them.

### Component / module decomposition

Everything lands in `packs/github/`. The profile table and the action set are
touched by the pattern slice, not here.

### State & control flow

Invocation reads the tree, resolves each rung against the profile row, and
emits a confirmation request per item. No resident state: the back-reference on
the remote item is the only durable link, which is what makes a later run
idempotent without a local database.

### Behavior & rules

A rung whose `Level` has no row is named as unmapped rather than guessed. A
rung below the floor produces a trace link on the floor issue or nothing. A
same-repository delivery brief produces nothing.

### Failure, edge cases & resilience

A refused confirmation aborts that issue and leaves the rest untouched. A
back-reference pointing at a deleted issue is reported rather than re-created,
because silently re-creating it is how an intentionally deleted issue returns.
A tree exceeding a vendor limit refuses before the first write, so a partial
projection is never left behind by a limit failure.

### Quality attributes (NFRs)

The board-doubling guardrail carries the pass/fail bar, measured as an item
count against the team's existing board at the first projection.

### Dependencies & integration

`gh` must be installed and authenticated — already this pack's stated
requirement. No new dependency.

## Tasks

### T1: every GitHub write runs through the bounded action set, and intake stays read-only

**Depends on:** spec:bounded-remote-create-action/T2

**Tests:**
- A write verb invoked without a confirmation refuses. Verifies *no write verb
  executes without the bounded action set's confirmation*.
- A confirmation shows the exact per-item payload and the protected-field set.
  Verifies *shows the exact per-item payload and the protected-field set*.
- One fresh confirmation creates exactly one issue; re-presenting it creates
  nothing. Verifies *one fresh confirmation creates exactly one issue*.
- `github-brief-intake` executes no write verb. Verifies *executes no write
  verb*.

**Approach:**
- The create lands in `github-refresh`, which already owns every GitHub write
  and already carries the action handlers. `github-brief-intake` keeps its
  refusal unchanged, so no trust boundary moves into a read-only skill.

**Done when:** the confirmation tests are green and the intake skill's refusal
is untouched.

**Touches:** packs/github/.apm/skills/github-refresh/**

### T2: the vendor limits come from a dated extract, not from literals

**Depends on:** none

**Tests:**
- The implementation resolves the nesting and per-level maxima from the
  recorded extract. Verifies *read from the recorded vendor extract*.
- A rung exceeding the per-level maximum refuses with the limit named.
  Verifies *refused with the limit named*.

**Approach:**
- Fan-out refuses because it is a capacity limit. Depth does not, because
  ADR-0127 D3 makes depth a collapse case — that branch is T3's.

**Done when:** no maximum appears as a literal and the fan-out refusal names
its limit.

**Touches:** docs/specs/tracker-working-view-github/notes/**, packs/github/.apm/skills/**

### T3: the reference tree projects onto an empty repository and collapses beyond GitHub's depth

**Depends on:** T1, T2, spec:tracker-projection-profile-table/T2

**Tests:**
- The reference tree yields one object per in-range rung; zero objects fails.
  Verifies *one GitHub object for every rung in the range*.
- A tree deeper than the nesting maximum collapses its surplus rungs onto the
  pattern's carrier and every surplus rung stays reachable in the rollup.
  Verifies *collapses its surplus rungs* and *the rollup resolves through each
  carrier*.
- Back-references resolve from both ends; no issue has a second parent.
- An agent-internal unit produces no managed object.

**Approach:**
- The carrier is the pattern slice's choice, not this slice's. Selecting one
  here would re-decide a variation point its owner settles.

**Done when:** the reference projection is complete and the deep-tree fixture
asserts the surplus rungs present rather than absent.

**Touches:** packs/github/.apm/skills/**

### T4: projecting onto a populated repository creates no duplicate

**Depends on:** T3

**Tests:**
- Projecting onto a repository already holding the team's issues yields no
  second managed object where a back-reference already exists. Verifies *no
  second managed object*.
- An unkeyed collision refuses, named, before any mutation. Verifies *refuses
  that rung and names it*.
- Same tree twice changes no issue count.

**Done when:** the populated-repository fixture creates nothing.

**Touches:** packs/github/.apm/skills/**

### T4a: repository scope is derived, and both sides of the brief rule are exercised

**Depends on:** T3

**Tests:**
- Scope derives from the canonical artifact's repository and the target's, with
  no static list. Verifies *repository scope is derived*.
- A same-repository brief produces no object; a cross-repository brief produces
  exactly one managed object. Verifies both brief criteria.

**Done when:** the paired fixture passes on both sides.

**Touches:** packs/github/.apm/skills/**

### T5: the return leg writes shaped intent onto an existing issue

**Depends on:** T1

**Tests:**
- A return-leg write is confirmed before transport and leaves the issue's
  existing fields intact.

**Done when:** a recorded confirmation transcript shows the write and the
untouched fields, and `packs/github/CHANGELOG.md` leads an entry.

**Touches:** packs/github/.apm/skills/github-refresh/**, packs/github/CHANGELOG.md

## Rollout

T1 is inert until T2 uses it. Each task is independently revertible, and the
pack is never left with the refusal removed and no confirmation in its place.

## Risks

- **A silent flatten passes review.** Mitigated by the deep-tree fixture
  asserting every surplus rung present and reachable, rather than asserting no
  error occurred.
- **Replacing a refusal weakens a safety rule.** Mitigated by narrowing the
  line rather than deleting it, and by the confirmation being the shared one
  rather than a GitHub-local invention.
- **`gh` behaviour differs across versions.** The transport is exercised
  through recorded transcripts, so a version change shows as a transcript
  mismatch rather than a silent behaviour change.

## Changelog

- 2026-09-24 — plan drafted.
