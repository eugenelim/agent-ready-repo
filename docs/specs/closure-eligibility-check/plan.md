# Plan: closure eligibility check

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - `packs/core/.apm/skills/close-work/SKILL.md` § Closeout procedure step 1 and
    § Exact immediate effect — the contract surface this change extends, and the
    stage separation it must not break.
  - `packs/core/.apm/skills/work-intake/scripts/intent_shape.py` module docstring
    — the surface placement rule deciding where a new rule may live. Read it
    before adding a rule to either surface.
  - Analogous implementation: `brief_shape.py`, shipped by
    [`brief-lifecycle-contract`](../brief-lifecycle-contract/spec.md), is the
    defining-home pattern this check consumes rather than copies; its test is
    `packs/core/tests/skills/author-delivery-brief/test_lint_brief_coverage.py`,
    which forbids a second `_BRIEF_STATUSES` home at line 521.
  - Analogous implementation: `lint-traceability.py`'s `recognize_intents`
    establishes that identity is the `Slug:` field, never the filename stem, and
    that a slug-less file contributes no node rather than falling back.
  - Named deviation: `close_work.py`'s stage separation was authored for
    single-file disposition effects, not for a graph read. The check is a
    read-only stage ahead of that sequence and reuses none of its confirmation
    machinery until a human has answered.

## Approach

The check is a read-only decision seam that runs before any mutation stage in
`close-work`. It builds an in-memory index for one decision, classifies, and
hands a packet to the human. Everything that mutates — the status write, the
registration move, the closure record — happens after the human answers, on the
existing confirmation machinery rather than a second one.

**The read set is bounded by the termini along the closure, not by the corpus.**
Finding descendants means inverting up-edges, and an up-edge can only be read by
opening the artifact that declares it — so discovery necessarily opens
candidates. What bounds it is that `Decomposed:` names the terminus at each
level, and a terminus names a collection: `children` means intents, `brief`
means briefs, `spec` means specs. So the candidate set at each level is the
collection its parent's terminus named, and the read set is the union of those
collections along the closure rather than every artifact in the repository.

This is the reading of the parent's § Boundary condition (c) that the plan rests
on: (c) bounds which part of the *graph* a verdict may rest on, and the parent
itself anticipated that inversion "is itself edge-shaped". Opening an artifact to
discover whether it is a member is not traversing a part of the graph the verdict
then uses. Where a terminus names a collection this check does not need, that
collection is never opened.

## Constraints

- The construction stays module-private and a test enumerates its callers.
- A verdict rests only on the ancestor chain and the descendant closure beneath
  each ancestor evaluated.
- Discovery opens only the collections the termini along that closure name.
- No new dependency, no new top-level directory, no new module boundary outside
  `close-work`'s existing `scripts/`.
- No cross-skill relative import. `guides/_shared/reference/skill-script-conventions.md`
  bans it and adapter projection breaks it, so the vocabularies this check
  consumes are reached by a mechanism T1 grounds against repository evidence —
  not by importing a sibling skill's module.
- `close-work`'s hard stops hold unchanged. The per-decision index is not the
  "second resolver" that stop names: a resolver is a durable surface a second
  consumer reads, and this index is built inside one decision's frame, exposes
  no entry point beyond the module-private construction AC-0026 pins, and is
  gone when the decision returns. AC-0023 is what makes that checkable rather
  than asserted. No lifecycle database, no global surface registry and no
  hidden receipt store are created.

## Construction tests

Every task leads with `Tests:`. Three properties need naming here because no
single task owns them:

- **The production entry point is the test surface for the verdict branches.**
  Driving the classifier directly is what makes a green predicate over a dead
  branch, and the not-eligible branch has never run in production. T3 owns
  proving reachability; later tasks may assert against the classifier once T3
  has established the path.
- **The differential is the assertion, not the verdict.** A test that shows
  not-eligible without showing the same path returning eligible on a terminal
  copy of the tree has shown the branch exists, not that it discriminates. The
  spec's Testing Strategy owns the precedent; AC-0016 and AC-0017 are its two arms.
- **Fixture trees are built by a helper, not written by hand.** T1 owns it. Nine
  tasks each hand-rolling a tree is where the trees quietly stop agreeing about
  what a corpus looks like.

## Durable-output map

| Durable output | Owning task | Evidence |
| --- | --- | --- |
| `close-work` skill contract | T8 | AC-0033's assertion over the contract text |
| Lifecycle guide section | T8 | Guide section describes the three verdicts |
| Intent terminality declaration | T1 | Parity test against the parent's Intent states table |
| Brief vocabulary consumption | T1 | Parity test against the shipped transition table |
| Release obligations | T8 | Changelog entry, `pack.toml` and `plugin.json` bumps |
| Read-bound measurement | T2 | `notes/verification-ledger.md` carries the depth sweep |


## Design (LLD)

### Design decisions

Owned by: T2, T3, T5

**The `Decomposed:` terminus routes the walk, and is the only thing that does.**
`Decomposed:` names no member — it admits `no`, or a date plus one terminus from
the shipped terminus vocabulary, which this plan cites rather than restates so a
terminus added upstream does not silently leave a hole here. The terminus says
which collection a descendant lives in, and the up-edge inversion finds the
members; T5's table-driven case is what fails when a new terminus has no verdict. This matters because a walk that inverts `Parent intent:`
across intents only returns eligible for `intent:lifecycle-and-closure`, whose
`Decomposed: 2026-09-23 brief` puts its only child in `docs/product/briefs/`.
That is a false eligible on a live artifact, and it is the case T2 pins.

**Refuse and not-eligible are different returns, not one return with a flag.**
A shared shape with a discriminant field is how the two collapse under a later
refactor: a caller reading truthiness sees the same thing for both. Separate
constructors make the collapse a type error rather than a silent one.

**Empty is observable because discovery is exhaustive within a collection, not
because the corpus is scanned.** The C2 distinction — empty because nothing
points here, or empty because the walk stopped early — needs the candidate set
to be complete. Reading the whole collection a terminus names makes it complete
without reading collections no terminus named, which is what keeps the bound in
§ Approach honest.

**The index is discarded by scope, not by a clear call.** Building it inside the
decision's own frame means there is no lifetime to get wrong and nothing to
assert about cleanup — AC-0023 becomes a statement about where the object is
constructed rather than about a teardown path that could be skipped.

### Data & schema

Owned by: T1, T2

No persisted schema changes and no `workspace.toml` write; the spec's
§ Follow-ons owns why. The in-memory index is slug → (kind, status, terminus) plus an
inverted parent-token → members map, both local to one decision. The one
declaration this change adds is the intent terminality predicate T1 owns.

### Interfaces & contracts

Owned by: T4

The check's public surface is one entry point called from `close-work`'s
closeout procedure, returning one of three verdict types. The descendant
construction beneath it is module-private, and a test enumerates its callers —
the weaker "no other caller exists" form is known not to hold here, because
slice 1 hit exactly that wall with `validate_supersession()` left public beside
`validate_corpus_scoped()`.

### Verification fixtures

Owned by: T4

**This sub-section is the only description of the differential fixture.** The
spec's Testing Strategy and the tasks reference it and do not restate its shape.

The fixture copies the real `work-item-capture-and-disposition` tree, measured
2026-09-26: an `Accepted` ancestor with `Decomposed: 2026-09-19 children`, four
child intents each `Accepted` and each carrying `Decomposed: 2026-09-19 spec`,
and five grandchild specs reached through `Discovery:`. Nine descendants across three node levels — ancestor, children, grandchildren —
which is two edges deep and clears the brief's "deeper than two levels" bar on
the node-level convention stated here; two artifact kinds; of which eight are live and one — `work-item-capture`
at `Shipped` — is terminal.

It exercises two termini in one walk, `children` then `spec`, and the `spec`
terminus is why AC-0002 carries `Discovery:` upward and AC-0020 inverts it downward: these grandchildren carry
`Brief: none` and reach their parent no other way. An implementation reading
`Parent intent:` and `Brief:` alone stops at depth 1 and returns eligible —
which is the C2 failure the parent intent warns about, so the halting case is
asserted as a control.

**The cross-kind control fixture, also defined here.** A copy of the
`intent:lifecycle-and-closure` tree as it stood when copied: an `Accepted`
intent whose `Decomposed: 2026-09-23 brief` reaches one brief, and that brief's
mapped specs. It is a **copy, not the live tree** — the live one gains a row
whenever a slice materializes, including in this change — so its expected set is
fixed at copy time and stated in the fixture. Its job is one assertion: an
intents-only walk returns eligible for it, which is wrong, and that wrong answer
is what makes the cross-kind step load-bearing.

`VISION-0001-ai-native-ecosystem` was rejected for the differential role: its closure is 24
descendants of which 23 are live at depth 5, so no copy of it can produce the
eligible arm.

The tests derive the expected live set from the fixture rather than naming
slugs, so a status move elsewhere in the corpus cannot silently change what is
asserted.

### Failure, edge cases & resilience

Owned by: T3, T5

- A slug-less artifact contributes no node, following `recognize_intents`. It is
  reported, not silently skipped, because a missing node changes a verdict.
- A cycle in the up-edges terminates on the visited set rather than recursing.
- An unresolvable `Parent intent:` token is a refusal, not an absent ancestor:
  the check cannot prove it has seen every ancestor.
- A descendant whose `Status` is absent or unrecognised is treated as live. The
  safe direction is not-eligible, because eligible authorises a terminal write.

### Quality attributes (NFRs)

Owned by: T2

**The cost driver is collection size, not closure size, and a saturated ladder
cannot show that** — it makes the two the same set, the same degenerate trap the
spec warns about for the live corpus.

**The collection-scaling fixture, defined once here.** A four-descendant closure
placed inside collections of 20, 100 and 400 artifacts. Measured 2026-09-26, a
decision opens 20, 100 and 400 artifacts respectively — **100 times the
four-member closure** at the largest — and a forty-descendant closure inside the
same 400-member collection also opens 400. Reads track the collection. The spec's
Testing Strategy and T2 reference this fixture and do not restate its numbers.

Two quantities follow, and only one is flat. **Reads per artifact** is 1.00 at
every depth, on a saturated ladder with branching factor 4 at depths 2 to 5.
**Reads per decision** tracks collection size: that ladder gives 21, 85, 341 and
1365 artifacts, which are the collection's figures, not the closure's. AC-0024
bounds the first as a per-artifact maximum; AC-0025 bounds the second by
confining which collections may be opened, which is the only bound reaching the
real cost. For scale, the live corpus indexes in 673 ms over 658 artifacts.

What is *not* bounded is the number of decisions — every descendant's terminal
transition fires a check on each ancestor. That cascade stays open in the
parent's § Unresolved questions.

### Dependencies & integration

Owned by: T1

Consumes three shipped contracts and defines none of them: the intent status
vocabulary and its value rules, the brief status vocabulary and its transition
table, and the `Outcome co-owner` and `closed-empty` declarations. Each has one
defining home and this change adds no second one.

`close-work` cannot reach any of those homes by a relative import —
`guides/_shared/reference/skill-script-conventions.md` bans cross-skill imports
because adapter projection breaks them, and no core skill script does it. T1
grounds the mechanism against what the repository already does and pins the
result with a parity test, so the criteria state the single-home obligation
rather than a call path.

## Tasks

### T1: Intent terminality has one declared home, and the brief home is consumed unchanged

**Depends on:** none
**Mode:** TDD

**Tests:**
- The intent terminality projection agrees with its upstream on every member of
  the shipped status vocabulary, iterated from that vocabulary so a new status
  fails rather than passing unnoticed (AC-0005). The upstream is the § The
  lifecycle › Intent states `Terminal` column of the intent whose `Slug:` is
  `lifecycle-and-closure` — located by slug, never by filename stem, because
  `intent-renumber-and-reissue` reissues intents at new ordinal prefixes.
- Discovery predicate for the parity test's home: it reads a repository
  governance document, and no test under `packs/core/tests/` does that today —
  every `docs/product/intents/...` reference there is a fixture or a tmp path.
  Constraint: the test must run in the repository's own suite without making a
  portable pack depend on repository-private content. Required outcome: the
  parity assertion runs in CI and reds on an upstream change. Verification mode:
  TDD. Kill condition: if no home satisfies both, route the placement question
  to the owner rather than silently coupling the pack.
- The brief terminal predicate agrees with the shipped transition table's
  no-outgoing-edge property on every brief status, and no second brief
  vocabulary is introduced (AC-0006).
- Each parity test is proven able to red, by mutation rather than by presence:
  flip one row of the upstream `Terminal` column in a copy, and one edge in a
  copy of the transition table, and assert the corresponding parity test fails.
  A guard that only checks the test still exists stays green against a test
  kept under the same name with a gutted body (AC-0007).
- `stub: true` — the two predicates are the contract surface here.

**Approach:**
- Seam decision: intent terminality is declared here because no shipped surface
  carries it — the status tuple is flat and the record-coherence table is about
  record presence, not terminality. Declaring it is cheaper and safer than
  reaching a sibling skill's module, which the cross-skill import ban forbids
  and which no sharing mechanism currently permits. Briefs are the opposite
  case: a shipped home exists, so it is consumed and not copied.

**Done when:** both parity tests are green and each iterates its vocabulary
rather than a hand-written list.

### T2: A decision opens each artifact once, and only the collections its termini name

**Depends on:** T1
**Mode:** goal-based check

**Tests:**
- A per-artifact **maximum** of one open per decision, asserted over the visited
  counter at depths 2, 3, 4 and 5, with a diamond fixture whose descendant is
  reachable by two paths named explicitly. An aggregate ratio is not used: a
  mean of one is satisfied by the diamond node opened twice and another opened
  zero times (AC-0024).
- A decision whose termini name one collection opens no artifact in any other
  collection, asserted by a directory-access recorder (AC-0025).
- Reads per decision never exceed the summed size of the named collections,
  asserted on the collection-scaling fixture where a four-member closure inside
  a 400-member collection opens 400 and not more (AC-0037).
- The bound is measured on the collection-scaling fixture defined in
  § Quality attributes (NFRs), because a saturated ladder makes collection and
  closure the same set and cannot distinguish the two bounds.
- After a decision returns, a write-raising filesystem double has raised
  nothing and an environment snapshot is unchanged (AC-0023).

**Done when:** the maximum holds at every swept depth including the diamond,
the access recorder shows no unnamed collection, and the counts are recorded in
`notes/verification-ledger.md`.

### T3: The walk is a full closure and crosses artifact kinds

**Depends on:** T2
**Mode:** TDD

**Tests:**
- A three-level fixture returns descendants from every level, not one hop
  (AC-0019).
- `intent:lifecycle-and-closure` resolves its child through the `brief`
  terminus and reaches the brief plus its mapped specs (AC-0020).
- An intents-only walk over the same fixture returns eligible — the control
  proving the cross-kind step is load-bearing rather than decorative.
- Identity resolves from `Slug:`, asserted on a fixture whose filename stem and
  slug differ. This guards the Always-do rail on identity rather than a
  criterion, and it is here because AC-0020's cross-kind walk is where a
  stem-keyed lookup would silently mis-resolve.

**Done when:** the cross-kind assertion and its intents-only control are green
in the same module.

### T4: The check fires from the production entry point and discriminates on a real tree

**Depends on:** T3
**Mode:** TDD

**Tests:**
- A terminal transition fires the check on its ancestors from within the
  closeout run, with no sweep and no schedule involved (AC-0001).
- Ancestors resolve from each declared up-edge, including a spec whose `Brief:`
  is `none` and whose only up-edge is `Discovery:` — the case reaching half the
  decomposed corpus, which a `Brief:`-only implementation misses (AC-0002).
- A `Discovery:` value in each of its three corpus forms — bare path, backticked
  path, markdown link — resolves to the same ancestor, and a value whose target
  is not an intent contributes no edge rather than failing (AC-0003).
- The entry point returns one of exactly three verdict types, asserted as a
  closed set rather than a truthiness check (AC-0004).
- The fixture described in § Design (LLD) › Verification fixtures returns
  not-eligible and names every live descendant, the expected set derived from
  the fixture rather than hard-coded (AC-0017).
- The differential: a copy of that fixture with **every** descendant in its full
  closure set terminal returns eligible through the same entry point (AC-0016).
  The count is not restated here; § Verification fixtures owns it.
- A caller-enumeration test lists every caller of the module-private
  construction and fails when one is added (AC-0026).

**Approach:**
- Ordering decision: this precedes the remaining verdict tasks because it
  establishes the production path is reachable. Tasks after it may assert
  against the classifier.

**Done when:** both arms of the differential are green, all three artifact
kinds resolve an ancestor, and the caller enumeration lists only the intended
entry point.

### T5: Every terminus and every state reaches a stated verdict

**Depends on:** T4
**Mode:** TDD

**Tests:**
- One case per refusal — AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013 —
  asserting the named precondition appears in the verdict.
- The eligible controls: `closed-empty` empty (AC-0014) and `direct-light`
  empty (AC-0015) both return eligible, keeping the empty-set refusals from
  passing for an implementation that refuses every empty set.
- A table-driven case over the cross-product of the shipped terminus vocabulary
  and empty/non-empty, failing when a terminus is added with no verdict mapped.
- One case per refusal ground constructed to also satisfy a non-refusal ground,
  asserting the refusal wins, so a precedence hole in any single ground reds
  (AC-0018).

**Done when:** every cell of that cross-product maps to an asserted verdict and
the table fails on an unmapped addition.

### T6: A decision re-reads its inputs and refuses on a stale base

**Depends on:** T5
**Mode:** TDD

**Tests:**
- A second decision over the same tree builds its own index and reuses nothing
  from the first, asserted by a counter that reds if a cached set is returned
  (AC-0021).
- A stale base refuses (AC-0022); a current base does not — the paired control.

**Done when:** both checks refuse on their negative case and pass on their
paired positive case.

### T7: The human sees a six-field packet and the check writes no status

**Depends on:** T6
**Mode:** TDD, plus manual QA for the real run

**Tests:**
- The packet carries all eight fields, asserted per field so dropping any one
  reds on its own (AC-0027).
- The packet carries the ancestor's stated outcome, read from its declared
  outcome section; an ancestor whose outcome section is absent reports that
  absence rather than omitting the field silently (AC-0038).
- The ratified child count reports resolved and declared separately, and a
  tree where the two differ shows both numbers rather than one (AC-0039).
- An ancestor declaring no `Outcome co-owner:` produces a stated-confidence
  line with no co-owner caveat; one declaring a co-owner does carry it — the
  paired arm, without which removing the caveat entirely would pass (AC-0040).
- An ancestor declaring `Outcome co-owner:` has that peer named in the packet,
  and the verdict is unchanged by the peer's state (AC-0028).
- The check runs to a verdict against a filesystem double that raises on any
  write, proving no path writes a `Status:` line (AC-0029).
- A record written after human confirmation round-trips through the shipped
  `Fulfilled:` value rule rather than matching a string (AC-0032).
- An artifact no disposition row reaches produces an absence report, not a
  default and not a failure, pinned by a fixture (AC-0034).
- An artifact a `cool-30-days`-eligible fixture does reach has that row
  reported, so an implementation that always reports absence reds (AC-0035).
- A declined confirmation and a not-yet-answered confirmation each leave no
  `Status:` write on the filesystem, driven through the real confirmation seam
  rather than the write-raising double, which cannot observe ordering (AC-0030).
- The packet names the closing intent's `workspace.toml` entry and collection
  as an effect the human must clear alongside the status write (AC-0031).
- Manual QA: one real intent-path closure decision, judged against the parent's
  § Validation hook line — the decider opened nothing the packet did not name.
  The brief path is out of this run's scope.

**Approach:**
- Seam decision: the absent-disposition case is pinned by a fixture, not the
  live contract. Slice 4 adds the row that would make this case stop occurring,
  and a test bound to the live contract would then pass vacuously.

**Done when:** the write-raising double raises nothing, the record round-trips
through the shipped rule, and the manual run's verdict against the predeclared
line is recorded in the verification ledger.

### T8: The agent-visible contract, the guide and the release obligations match the check

**Depends on:** T7
**Mode:** goal-based check

**Tests:**
- `close-work/SKILL.md` contract text states the trigger, all three verdict
  names and the closure record (AC-0033).
- The skill's eval harness covers the three verdicts.
- `lint-brief-coverage.py`, `lint-spec-status.py`, `lint-traceability.py`, the
  intent corpus lint and `lint-contract-item-alignment.py` all exit 0.
- The guide section in `guides/core/how-to/close-and-disposition-work.md` names
  all three verdicts and what a human decides at each (AC-0036).

**Done when:** the five lints exit 0, AC-0033's assertion is green, and the
guide section renders.

## Rollout

- **Delivery:** big bang within `close-work`; the check is additive and no
  artifact changes shape. Nothing this slice ships is persisted, so reverting
  the PR is a complete rollback.
- **Out of scope, and not persisted here:** the `workspace.toml` registration
  move. The spec's § Follow-ons owns the reason and the ordering edge.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none beyond task order. Every surface this slice
  consumes is already delivered; the delivery brief's § Spec map owns those
  statuses and this section does not restate them.

## Risks

- **The cascade this design creates is unbounded in decision count.** AC-0024,
  AC-0025 and AC-0037 bound one decision; nothing bounds how many fire as the
  ladder fills. Recorded open in the parent's § Unresolved
  questions, carried in the spec's Assumptions, and deliberately not closed here.
- **A false eligible is the expensive failure direction.** It authorises a
  terminal write on live work. Every ambiguous case therefore resolves toward
  refuse or not-eligible, which is why an unrecognised status counts as live.
- **The guide section can drift from the shipped verdicts.** T8 owns it, but
  nothing mechanically ties guide prose to the three verdict types.

## Changelog

- 2026-09-26 — drafted.
- 2026-09-26 — spec approved by eugenelim. Taken on a `Findings` result rather
  than a `Clean` one; `spec.md`'s `Approved:` line records the review trend and
  the residual risk accepted.
- 2026-09-27 — AC-0027 amended from six packet fields to eight, and AC-0038,
  AC-0039 and AC-0040 added, on owner authority after the first manual run
  returned *cannot decide* against a real eligible closure. The engine could
  not record the amendment transitions: upstream moved cohort state to schema
  2 mid-run, so authority and evidence are recorded here and in
  `notes/verification-ledger.md` instead.
- 2026-09-26 — plan approved by eugenelim, on the same basis. T1's
  brief-terminality mechanism stays a discovery predicate carrying a kill
  condition: if no route keeps a single defining home, T1 stops and routes the
  question to the owner rather than restating a vocabulary.
