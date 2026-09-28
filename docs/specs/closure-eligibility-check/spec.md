# Spec: closure eligibility check

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-09-26 by eugenelim, spec and plan together. **Taken on a `Findings` result, not a `Clean` one**, and recorded here because `work-loop` expects a Clean pre-EXECUTE review and this transition did not have one. Four adversarial spec-mode rounds returned 8, 4, 4 and 2 Blockers, and a shaping review run fresh after the slice was narrowed returned 4; every finding from the final round of both reviewers was applied, and no round was re-run to confirm the result. The owner accepted the residual risk § Assumptions records — three unratified deviations from the parent's § Boundary conditions, and a brief-terminality read mechanism still carried as a T1 discovery predicate with a kill condition rather than a settled design.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0119
- **Brief:** brief:intent-lifecycle-and-closure
- **Discovery:** none
- **Contract:** none
- **Shape:** service

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

## Outcome

When a maintainer closes a piece of work, `close-work` tells them which intents
above it can now close too, and refuses loudly when it is not entitled to an
opinion. Every verdict names its ground — the missing
precondition, the live descendant that blocks, or the evidence a human is being
asked to decide on — and no status is ever set by the check itself.

## What Changes

- A closure check fires on the **intent** ancestors of any artifact reaching a
  terminal state — inside `close-work`'s closeout procedure, on the run that is
  already happening. A brief is walked through and read as a descendant; it is
  not evaluated as an ancestor, because no brief carries the `Decomposed:`
  field every precondition in the flow reads.
- A three-way verdict — refuse, not eligible, eligible — replaces the absence
  of any answer. It lives in `close-work`'s skill contract and its deterministic
  script seam.
- A descendant set built per decision by inverting declared up-edges, crossing
  intent → brief → spec, and discarded when the decision ends.
- A closure record written on a terminal transition, carrying date, decider and
  the evidence they saw.
- One reader-facing guide page section covering the closure flow.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | The closure flow is new agent-visible behaviour | `packs/core/.apm/skills/close-work/SKILL.md` | `close-work` maintainer | The skill contract states the trigger, the three verdicts and the record | Skill text matches the shipped check |
| User-facing promise | Maintainers invoke this flow directly | `guides/core/how-to/close-and-disposition-work.md` § Review the closeout preview | Platform Core maintainer | Guide section covering states, transitions and the closure flow | Guide describes the shipped verdicts |
| Decision rationale | Ownership of the `[backlog].open` writer was decided | `docs/product/intents/FEAT-0005-lifecycle-and-closure.md` § Boundary item 7 | eugenelim | The recorded 2026-09-26 owner decision and its three bounds | Already recorded; verify unchanged |
| Interface compatibility | A brief's terminality is read from an upstream home this slice must not fork | the parity test under `close-work`, reading `brief_shape.py` as its upstream | `close-work` maintainer | AC-0006's derivation test against the shipped transition table | The test exists and fails when that table changes |
| Release history | `packs/core/` content changes | `changelog.md` and the pack version bumps | release workflow | Changelog entry plus `pack.toml` and `.claude-plugin/plugin.json` bumps | Version bump matches the change class |
| Reusable learning | The read bounds and the one real closure run were measured, not assumed | `notes/verification-ledger.md` in this spec directory | implementing session | The depth sweep, the collection-scaling measurement, and the manual run's verdict against its predeclared line | Ledger carries all three; a missing manual-run verdict blocks closeout |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Resolve every descendant state from the artifacts at decision time.
- Keep refuse and not-eligible distinct in every code path, every message and
  every test.
- Read an artifact's identity from its `Slug:` field, never from the filename
  stem — measured 2026-09-26, 22 of 153 intent filenames carry an ordinal
  prefix.
- Normalize a field value by discarding a trailing HTML comment first and
  stripping surrounding backticks second, through `intent_shape.normalize_value`.
- Name the live descendant, and its state, in every not-eligible verdict.

### Ask first

- Adding any preamble field, to either artifact kind.
- Changing `close-work`'s disposition contract rows — slice 4 owns the one
  change this family makes to them.
- Widening the walk beyond the ancestor chain and the descendant closure
  beneath each ancestor being evaluated, or opening a collection no
  `Decomposed:` terminus along that closure names.
- Moving a brief-status or intent-status vocabulary out of its current home.

### Never do

- Never create a new module boundary, top-level directory, or dependency for
  this check; it extends `close-work`'s existing script seam.
- Never persist the descendant set, or carry it across decisions.
- Never set a terminal status from a count, or from anything but a human
  decision on the presented evidence.
- Never make the descendant construction reachable from `validate_live_intent()`
  or from the corpus lint's entry point.
- Never let the closure check itself write to `workspace.toml`. `close-work`'s
  existing brief-path entry move is unchanged and is not what this forbids.
- Never restate a status vocabulary that has a shipped defining home **except**
  as a parity-pinned read-side projection: permitted only where no legal route
  to that home exists, and only with a parity test asserting the projection
  against its upstream. A restatement without that test is forbidden. This
  exception exists because a cross-skill relative import, a copied module, and
  a new `shared-libs` boundary are each banned by a rail this change is under,
  so a projection is the only remaining shape.

## Testing Strategy

Each criterion appears in exactly one group below. Every task states its mode.

- **Trigger, ancestor resolution and the closed return set — AC-0001, AC-0002,
  AC-0003, AC-0004:** TDD, driven through
  `close-work`'s production entry point. What can fail is that the check never
  fires on a real transition, so exercising the classifier alone would not
  observe it.
- **The terminality projections — AC-0005, AC-0006, AC-0007:** TDD. Each
  declaration carries a parity assertion against the upstream home it is
  derived from — the parent intent's § Intent states table for intents, the
  shipped brief transition table for briefs. AC-0007 is what keeps them
  projections rather than rival definitions: removing either parity test fails
  the suite, so the declarations cannot drift from their sources unnoticed.
- **The refusals — AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013:** TDD,
  one case per refusal. Each names a distinct missing precondition with its own
  remedy.
- **Verdict precedence — AC-0018:** TDD. An input constructed to satisfy a
  refusal ground and a non-refusal ground at once returns the refusal, asserted
  once per refusal ground so a precedence hole in any single one reds.
- **The eligible arms — AC-0014, AC-0015:** TDD. These are the paired
  controls that stop the refusals from passing for an implementation that
  refuses everything; slice 1's review caught a criterion set made only of
  refusals as a Blocker.
- **The not-eligible branch and its differential — AC-0016, AC-0017:** TDD
  through the production entry point. The plan's § Design (LLD) › Verification
  fixtures owns the tree's description and this section does not restate it.
  AC-0017 asserts the verdict names every live descendant; AC-0016 asserts the
  same path over a copy with every descendant set terminal returns eligible.
  The test derives the expected live set from the fixture rather than naming
  slugs, so a status move elsewhere in the corpus cannot silently change what
  is asserted.
- **The walk — AC-0019, AC-0020:** TDD. AC-0020's control is that an
  intents-only walk returns eligible for `intent:lifecycle-and-closure`, whose
  `Decomposed: 2026-09-23 brief` routes into a brief; that wrong answer is what
  makes the cross-kind step load-bearing rather than decorative.
- **The staleness refresh — AC-0021, AC-0022:** TDD, each with a paired positive
  case. A refusal check with no passing case cannot distinguish a working gate
  from one that refuses everything.
- **Per-decision lifetime — AC-0023:** goal-based check, instrumented by a
  write-raising filesystem double and an environment snapshot taken before and
  after the decision.
- **The read bounds — AC-0024, AC-0025, AC-0037:** goal-based checks with different
  instruments, because one fixture cannot serve both. AC-0024's per-artifact
  maximum is measured on a synthetic saturated ladder at depths 2 to 5,
  including a diamond node reachable by two paths; a mean would go green on
  exactly that node. AC-0025's collection confinement is measured on a fixture
  where the collection is much larger than the closure — 4 descendants inside
  collections of 20, 100 and 400 — because a saturated ladder makes collection
  and closure the same set and cannot tell the bounds apart. AC-0037's
  per-decision maximum is asserted on that same collection-scaling fixture.
- **The enforcement-point boundary — AC-0026:** TDD as a caller enumeration over
  the module-private construction. A reachability differential against
  `validate_live_intent()` is not used here, and § Assumptions records that
  substitution against the parent's condition (b) for the owner to confirm.
- **The packet — AC-0027, AC-0028, AC-0031, AC-0038, AC-0039, AC-0040:** TDD
  for the field set. The three added criteria come from the manual run, not
  from review: a decider given the six-field packet for a real eligible
  closure returned *cannot decide*, because the packet established that the
  tree was finished and never said what the intent promised. AC-0040 is a
  negative: the co-owner caveat must not fire when no co-owner is declared.
  Also TDD for the field set, including
  AC-0031's naming of the registration entry the human must clear, plus manual
  QA for
  one real closure decision, judged against the line the parent's § Validation
  hook sets — that the decider opened nothing the packet did not name — and
  scoped to the intent path only.
- **The status write and the record — AC-0029, AC-0030, AC-0032:** TDD.
  AC-0029's instrument is a write-raising double; AC-0030 needs a different
  one, because a double that raises on every write cannot observe ordering —
  it drives a declined and a not-yet-answered confirmation and asserts no write
  reached the filesystem on either path. AC-0029 is
  instrumented by a write-raising filesystem double; AC-0032 round-trips the
  written value through the shipped rule rather than matching a string.
- **The disposition lookup — AC-0034, AC-0035:** TDD against fixtures, not the
  live contract. AC-0035 is the accepted arm without which an implementation
  that always reports absence passes. Fixtures rather than the live
  contract: slice 4 adds the row that would make this case stop occurring, and
  a test bound to the live contract would then pass vacuously.

- **The agent-visible contract and the guide — AC-0033, AC-0036:** goal-based
  checks over `close-work/SKILL.md` and
  `guides/core/how-to/close-and-disposition-work.md`. Both are text assertions
  over shipped reader-facing surfaces, which is the only instrument that can
  red when prose drifts from the three verdicts.

## Acceptance Criteria

- [x] **AC-0001.** A terminal transition on an artifact fires a closure check
      on each **intent** ancestor above it, on the `close-work` run performing
      that transition. No sweep and no schedule reaches the check. A brief is
      walked through to reach the intent above it and is never itself evaluated
      as an ancestor.
- [x] **AC-0002.** The ancestor chain resolves from the declared up-edge each
      artifact kind carries: an intent's and a brief's `Parent intent:`, and a
      spec's `Brief:` or `Discovery:` value. A spec carries no `Parent intent:`
      field and reaches a `spec`-terminus intent only through `Discovery:`, so
      an implementation reading `Parent intent:` and `Brief:` alone resolves no
      ancestor for half the decomposed corpus — measured 2026-09-26, 12 of 24
      decomposed intents carry a `spec` terminus.
- [x] **AC-0003.** A `Discovery:` value is resolved across the three forms the
      corpus uses — measured 2026-09-26: 17 bare repository-relative paths, 9
      backticked paths, and 3 markdown links. Resolution reads the target
      artifact's `Slug:` to obtain identity, and a value whose target is not an
      intent contributes no ancestor edge rather than failing the decision.
      `intent_shape.normalize_value` does not reduce the link form, so a
      mechanism relying on it alone leaves `rendered-page-visual-inspection`
      unresolvable against its `spec`-terminus parent.
- [x] **AC-0004.** The check returns exactly one of `refuse`, `not-eligible`, or
      `eligible`. Every reachable path returns one of the three, and no path
      collapses `refuse` into `not-eligible`.
- [x] **AC-0005.** This spec declares the terminal intent statuses to be
      exactly `Fulfilled`, `Withdrawn`, `Cancelled` and `Superseded`, and that
      declaration is the only place the check reads intent terminality from. A
      parity test asserts it against the parent intent's § The lifecycle ›
      Intent states `Terminal` column, iterated over the shipped status
      vocabulary so a status added upstream fails rather than passing unnoticed.
- [x] **AC-0006.** A brief's terminality is decided by a two-part predicate
      over the shipped brief vocabulary: a status outside that vocabulary is
      **live**, and a status inside it with no outgoing edge in the shipped
      transition table is terminal. The unknown status resolves live because
      eligible authorises a terminal write, so the safe direction is the one
      that refuses to authorise it.
- [x] **AC-0007.** Both terminality predicates are parity-pinned projections,
      each carrying a test that asserts it against the upstream home it derives
      from and reds when that upstream changes. Neither is authoritative. The
      intent projection additionally states what it is **not**:
      `workspace_status_engine._TERMINAL_STATUS_BY_KIND` maps `intent` to
      `{Accepted, Fulfilled}`, which is collection-routing terminality — the
      status at which a kind rests in its collection — and not lifecycle
      terminality. Reusing it would make `Accepted` terminal, which is the
      false-eligible direction.
- [x] **AC-0008.** An ancestor intent whose `Status` is neither `Accepted` nor
      terminal refuses, naming the unreached `Accepted` precondition.
- [x] **AC-0009.** An ancestor intent that has already reached a terminal state refuses,
      naming that it is already closed.
- [x] **AC-0010.** An ancestor intent whose `Decomposed:` is absent or `no` refuses,
      naming the absent ratified delivery set.
- [x] **AC-0011.** An ancestor whose `Decomposed:` terminus expects artifact
      children but whose descendant set is empty refuses, naming the empty set.
- [x] **AC-0012.** An ancestor whose `Decomposed:` terminus is `closed-empty`
      but whose descendant set is non-empty refuses, naming the descendants the
      terminus says do not exist.
- [x] **AC-0013.** An ancestor whose `Decomposed:` terminus is `direct-light`
      but whose descendant set is non-empty refuses, naming those descendants.
- [x] **AC-0014.** An ancestor whose `Decomposed:` terminus is `closed-empty`
      and whose descendant set is empty returns eligible on that ground, absent
      a refusal ground another criterion states.
- [x] **AC-0015.** An ancestor whose `Decomposed:` terminus is `direct-light`
      and whose descendant set is empty returns eligible on that ground, absent
      a refusal ground another criterion states. That terminus records children
      that are not artifacts, so no artifact walk can observe them.
- [x] **AC-0016.** An ancestor that has reached `Accepted`, carries a
      `Decomposed:` terminus expecting artifact children, and whose full
      descendant closure is non-empty and entirely terminal returns eligible on
      that ground, absent a refusal ground another criterion states.
- [x] **AC-0017.** An ancestor with at least one non-terminal descendant in its
      full closure returns not-eligible on that ground, absent a refusal ground
      another criterion states, and the verdict names every live descendant's
      slug and its current state.
- [x] **AC-0018.** A refusal ground outranks both the not-eligible and the
      eligible grounds. Where an input satisfies a refusal criterion and also
      satisfies AC-0014, AC-0015, AC-0016 or AC-0017, the check refuses, so
      exactly one verdict is defined for every input.
- [x] **AC-0019.** The descendant set is the full closure beneath the ancestor,
      not one hop.
- [x] **AC-0020.** The closure crosses artifact kinds, routed by the ancestor's
      `Decomposed:` terminus, and every terminus in the shipped vocabulary that
      names an artifact collection states the up-edge inverted to reach it: a
      `children` terminus inverts `Parent intent:` over intents, a `brief`
      terminus inverts `Parent intent:` over briefs and then inverts `Brief:`
      over specs to reach that brief's specs, and a `spec` terminus inverts
      `Discovery:` over specs. Every arm inverts a declared preamble field; no
      arm reads a body table, including a brief's Spec map. A terminus naming no artifact collection inverts
      nothing.
- [x] **AC-0021.** Every descendant state a verdict rests on is resolved during
      the decision that uses it. No decision reuses a state, an index, or a
      verdict built by an earlier decision.
- [x] **AC-0022.** A closure decision refuses when HEAD is not current against
      the merge target at the closing edge, and does not refuse on that ground when it is current.
- [x] **AC-0023.** The descendant set is written to no file and no environment
      variable, asserted by a write-raising filesystem double and an environment
      snapshot compared across the decision.
- [x] **AC-0024.** A closure decision opens each artifact at most once. The
      limit is a per-artifact maximum over every artifact the decision opens,
      candidates included, measured from the check's entry to its verdict; a
      visited set is the enforcement mechanism; and the input that makes it fire
      first is a diamond, where one descendant is reachable from an evaluated
      ancestor by more than one path.
- [x] **AC-0025.** A closure decision opens only the collections the
      `Decomposed:` termini along its closure name. A collection no terminus
      along that closure names is never opened. The enforcement mechanism is
      that discovery is driven by the terminus at each level rather than by a
      directory scan, and the input that makes it fire first is an ancestor
      whose terminus names one collection while another collection exists.
- [x] **AC-0037.** A closure decision opens no more artifacts than the summed
      size of the collections the `Decomposed:` termini along its closure name.
      The limit is measured per decision from the check's entry to its verdict;
      its enforcement mechanism is that discovery never recurses outside those
      collections; and the input that makes it fire first is a closure whose
      termini name every collection at once. Asserted on the collection-scaling
      fixture, where a four-member closure inside a 400-member collection opens
      400 artifacts and not more. This is the bound the parent's § Boundary and
      the brief's § Candidate delivery slices both owe, stated as a derivation
      because the absolute number moves with the corpus.
- [x] **AC-0026.** The descendant construction is module-private, and a test
      enumerates its callers. Adding a caller outside the closure check's own
      entry point fails that test.
- [x] **AC-0027.** An eligible verdict presents an evidence packet carrying
      eight fields: the decision date, the decider, the ancestor's **stated
      outcome**, the ancestor's ratified `Decomposed:` value, a **ratified
      child count** of the form "N of N", the basis on which the outcome was
      verified, a per-descendant verdict with an evidence locator for each,
      and a stated-confidence line naming what was not checked.
- [x] **AC-0038.** The packet carries the ancestor's stated outcome, read from
      its declared outcome section. A decider asked whether finishing the tree
      delivered the intent cannot answer from terminality alone, because
      terminality says the recorded children finished and says nothing about
      what was promised.
- [x] **AC-0039.** The packet's ratified child count states how many
      descendants the walk resolved against how many the ratified
      decomposition declares, and the two are reported separately rather than
      as one number. "Every descendant is terminal" is silent about a
      descendant that was never created, so a completeness claim cannot be
      derived from a terminality claim.
- [x] **AC-0040.** Where the ancestor declares no `Outcome co-owner:`, the
      stated-confidence line carries no co-owner caveat. A caveat that fires
      unconditionally sends a decider looking for a risk the packet has
      already ruled out.
- [x] **AC-0028.** Where the ancestor declares an `Outcome co-owner:`, the packet
      names that peer. The verdict is not gated on the peer's state, which sits
      outside the closure the check is entitled to read.
- [x] **AC-0029.** The check writes no `Status:` value.
- [x] **AC-0030.** No `Status:` write reaches the filesystem on a path where
      the human declined the presented evidence or has not yet answered.
- [x] **AC-0031.** Where the closing intent has a `workspace.toml`
      registration, the evidence packet names that entry and its collection as
      an effect the human must clear in the same confirmed action as the status
      write. The check performs no such write itself. Leaving the entry in
      `backlog.open` with a non-`Draft` status is what
      `workspace-queue-reconciliation` reports as `impossible_transition`, and
      no collection admits a closed intent, so an uncleared entry is
      permanently non-dispatchable.
- [x] **AC-0032.** A terminal transition on an intent writes a closure record
      whose value satisfies the shipped `Fulfilled:` value rule — an ISO date, a
      space, then non-empty text naming the decider and the evidence — asserted
      by passing the written value back through that rule.
- [x] **AC-0033.** `close-work`'s § Closeout procedure states the trigger, all
      three verdict names as a set, and the closure record. The assertion is
      scoped to that section's body: measured 2026-09-26, the skill file already
      contains 13 occurrences of refusal and eligibility wording in its
      disposition contract, so a document-wide substring check passes before
      any work is done.
- [x] **AC-0034.** The product-bet disposition lookup is optional. When no
      disposition row's eligibility clause reaches the artifact, the check
      reports that absence and continues; it neither defaults to a row nor fails
      the decision.
- [x] **AC-0035.** An artifact a disposition row's eligibility clause does
      reach has that row reported. Without this arm an implementation reporting
      absence unconditionally, never consulting the contract, satisfies the
      absence criterion.
- [x] **AC-0036.** `guides/core/how-to/close-and-disposition-work.md`
      § Review the closeout preview names all three verdicts and says what a
      human decides at each. The assertion is scoped to that section's body.

## Follow-ons

- eugenelim, [CAP-0003](../../product/intents/CAP-0003-workspace-coordination-reorganization.md) —
  moving a terminal intent's `workspace.toml` registration out of
  `[backlog].open`. **This slice does not write it.** No collection admits a
  closed intent today: `backlog.closed` admits the `defect` kind only, and every
  shaping collection refuses a terminal intent, so the only implementation that
  satisfies a move is a deletion. CAP-0003 owns that schema, and
  [STRAT-0001](../../product/intents/STRAT-0001-graph-powered-sdlc.md) already
  records the same gap. **Slice 2 takes an ordering edge on CAP-0003 for this
  write only**; the rest of the slice is unordered against it.
- eugenelim, `brief:intent-lifecycle-and-closure` — the brief closure path and
  a ratification concept for a brief's delivery set. Measured 2026-09-26, zero
  of 17 briefs carry `Decomposed:`, so the preconditions gating steps 2 to 5
  have nothing to read on a brief. That brief's § Candidate delivery slices
  records the narrowing and leaves the home to the owner's next cut decision.
- eugenelim, `brief:intent-lifecycle-and-closure` slice 4 — the retention
  eligibility row for work that closed without delivering. AC-0034 reports the
  absence this spec leaves in place; slice 4 fills it.
- eugenelim, [FEAT-0001](../../product/intents/FEAT-0001-intent-identity-and-registration.md) —
  **a ratified-membership field.** `Decomposed:` records a date and a terminus
  and names no member, so a packet can say a decomposition was ratified and
  never what it covered. On a one-child tree that is the whole question, and
  the second manual run declined on exactly it. Mechanically closable only by
  a field that names members.
- eugenelim, `brief:intent-lifecycle-and-closure` — **the packet cannot
  distinguish a complete delivery from an incomplete one.** Both manual runs
  found this; the second stated it precisely: the packet supports a decline
  and cannot support an approve, because nothing maps outcome clauses to
  descendants. A mechanical mapping is not available — which descendant
  delivered which clause is the judgement the parent's Guardrail keeps with
  the human — so closing this needs a shaping decision about what the packet
  owes, not an implementation change.
- eugenelim, parent intent § Validation hook — **the predeclared line is
  weaker than the property.** "The decider opened nothing the packet did not
  name" is satisfied by a decider who declines to engage, as the first run
  showed. "The decider could reach a decision from the packet alone" is the
  line that produced a finding. Any slice reusing the current wording
  inherits the weakness.
- eugenelim, `brief:intent-lifecycle-and-closure` — **two packet fields read
  two ways.** `workspace registration` renders an unlabelled path/collection
  pair, so `backlog.open` reads either as a register section or as a live
  open item closure would strand; and `disposition row: None` cannot be told
  from "none required".
- eugenelim, [`brief:intent-identity-and-registration`](../../product/briefs/intent-identity-and-registration.md)
  § Post-Ready decisions — a declared carve-out marker and a declared citation
  or claims marker, both recorded there 2026-09-26. Without the first, C1's
  refusal is unexpressible; without the second, the parent's staleness check 3
  is. Neither blocks this slice.

## Assumptions

- Technical: C1 has no expressible verdict. Measured 2026-09-26, the string
  `carve` appears nowhere in `intent_shape.py`, and the only shipped signal is
  the optional `Outcome co-owner:` field. Resolving that peer's state would read
  an artifact outside the closure the parent's § Boundary condition (c) admits,
  so AC-0028 puts the declaration in the packet and gates no verdict on it. C1's
  refusal therefore does not ship in this slice (settled by: eugenelim, under
  `brief:intent-identity-and-registration`, whose § Post-Ready decisions carries
  the handoff recorded 2026-09-26).
- Technical: the parent's staleness check 3 — that the artifact's own claims
  still hold — has no expressible criterion. An intent's citations live in its
  body, and the brief's § Scope forbids gating a transition on anything read out
  of a body, so a citation-resolution refusal cannot be authored without a
  declared field. The check presents the ancestor's claims for human
  revalidation as part of AC-0027's packet instead (settled by: eugenelim, under
  `brief:intent-identity-and-registration`, whose § Post-Ready decisions carries
  the handoff recorded 2026-09-26). This is a partial non-delivery of the
  parent's § Staleness refresh at closure, which assigns specifying all three
  checks to this child: checks 1 and 2 ship as AC-0021 and AC-0022.
- Technical: this spec substitutes a caller enumeration (AC-0026) for the
  reachability differential the parent's § Boundary condition (b) names. The
  construction lives in `close-work`, which `validate_live_intent()` has no path
  to, so a differential would be green before any work was done and could never
  red. The enumeration can fail when a caller is added (settled by: eugenelim,
  lifecycle owner, as an amendment to (b) if the substitution is not accepted).
- Technical: condition (c) admits an ancestor chain "resolved upward from
  declared `Parent intent:` up-edges", and AC-0002 also resolves upward from a
  spec's `Brief:` and `Discovery:`. It has to: a spec carries no
  `Parent intent:` field, so the literal reading reaches no ancestor from the
  artifact kind that most often reaches terminal. Recorded as a widening of
  (c)'s edge set, not just of its read set (settled by: eugenelim, lifecycle
  owner, as an amendment to (c)).
- Technical: whether condition (c) permits opening a collection to discover
  membership. The plan's § Approach states the reading it rests on — that (c)
  bounds the graph a verdict uses, not the files discovery opens — because
  inversion cannot find a descendant without reading candidates. AC-0025 bounds
  which collections may be opened (settled by: eugenelim, lifecycle owner, as an
  amendment to (c) if the reading is wrong).
- Technical: whether the cascade stays affordable once the ladder fills.
  AC-0024, AC-0025 and AC-0037 bound one decision; the number of decisions grows as every
  descendant transition fires a check on each ancestor. Recorded open in the
  parent's § Unresolved questions and not closed here (settled by: a measurement
  after the corpus is substantially decomposed).
- Product: whether a `Superseded` ancestor should be checked at all — the
  supersession pointer names a replacement that may itself be live, and no
  artifact states whether the replacement's descendants bear on the superseded
  intent's closure (settled by: eugenelim, lifecycle owner).
