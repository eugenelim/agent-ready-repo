# Verification ledger: load-bearing-claim-grounding

Execution observations. The spec holds the contract and the plan holds the
strategy; neither is edited to record what happened here.

## T1 and T2 — landed 2026-09-17

The routing rule replaces the one-per-candidate cardinality in both of its
homes — the step heading and the load-bearing body sentence — and keeps the
`not a sweep` bound. `packs/core/.apm/skills/new-spec/SKILL.md` body is 734
lines as the linter counts it — 745 file lines less an 11-line frontmatter, against the 1000-line error, and carries no
install path. Both pointer
surfaces carry the anchor `load-bearing-claim-routing` and no table row.

**A line-oriented grep reported `not a sweep` absent while it was present.** The
phrase hard-wraps. Every assertion in the suite therefore reads
whitespace-flattened text, and the module docstring says why. This is the same
wrapping trap that made `one targeted check per candidate assumption`
unsearchable when the cardinality's second home was being located.

### Mutation proof — every arm reddens a named case

| Arm removed | Exit | Case |
| --- | ---: | --- |
| six consequences → seven | 1 | `test_the_six_consequences_are_exactly_the_contracted_ones` |
| `not a sweep` bound | 1 | `test_the_sweep_bound_is_retained` |
| cardinality reintroduced | 1 | `test_the_cardinality_is_absent_from_both_homes` |
| a routing key renamed | 1 | `test_row_keys_equal_the_fixture_exactly` |
| a routing row deleted | 1 | `test_row_keys_equal_the_fixture_exactly` |
| a routing row duplicated | 1 | `test_keys_are_unique` |
| kill condition dropped from the five fields | 1 | `test_the_unstarted_task_destination_names_five_fields` |
| a cut shape identifier returns | 1 | `test_no_cut_identifier_is_named` |
| one word edited inside step 5a | 1 | `test_step_5a_matches_the_pre_change_digest` |
| the `work-loop` pointer removed | 1 | `test_each_surface_carries_the_anchor_identifier_verbatim` |
| the guide pointer removed | 1 | `test_each_surface_carries_the_anchor_identifier_verbatim` |
| the routing table gains a second home | 1 | `test_exactly_one_shipped_surface_carries_the_routing_table` |

**The uniqueness arm was vacuous on its first run, and the mutation is why we
know.** It used `re.findall(r"^\|\s*` … `", …, re.M)`. The routing table is
indented inside a numbered list item, so that anchor matched nothing and the arm
compared an empty list against itself — it passed a duplicated row. Both the
uniqueness arm and the destination assertions now share one stripped-line parse,
`_routing_rows`, which returns ordered pairs rather than a mapping, because a
mapping collapses a duplicate and makes uniqueness undecidable from it.
`test_the_row_parse_is_not_vacuous` pins the parse at three rows so an empty
parse can never make uniqueness trivially true again.

## Post-gates review round 1 — ten findings, all sustained (2026-09-17)

Seven Blockers, three Concerns. Six of the seven Blockers were one class: a
control asserting less than the criterion it claimed to prove.

| # | Defect | Confirmed by |
| --- | --- | --- |
| 1 | a **third** home implied the one-check cardinality — the anti-pattern list's "the one check you attempted" | reading `SKILL.md`; AC-0009 names two homes and there were three |
| 2 | the adopter guide paraphrased all three destinations while claiming to only point at them | reading the guide against the *Always do* single-home rule |
| 3 | the taxonomy arm searched for three labels, so a fourth passed | mutation — adding a `**Timing**` category stayed green |
| 4 | the consequence arm counted six without checking which six | mutation — substituting one consequence stayed green |
| 5 | the placement arm asserted a fragment, so moving the predicate out passed | mutation — relocating the predicate stayed green |
| 6 | two destinations had no semantic arm; dropping "bounded spike" passed | mutation |
| 7 | AC-0008's fixture used four demand strings the criterion does not state | reading the criterion against the fixture |
| 8 | the workspace entry carried the superseded scope and a stale status | reading it against the approved spec |
| 9 | the task-local routing observation over-counted its filled fields | reading `T1`'s `Tests` |
| 10 | the deviation admission called the states' agreement luck and omitted what was skipped | reading it against the wave protocol |

Every arm now compares against a literal fixture transcribed from its criterion,
and the taxonomy, consequence and placement arms parse a complete set rather
than searching for members.

**Two mutations reported GREEN and had never applied.** Substituting a
consequence and relocating the firing predicate both looked like controls that
do not fire; both anchors had been written against unwrapped text while the file
hard-wraps mid-phrase. Re-applied against the real wrapping, both redden. A
mutation that does not change the file is indistinguishable in the output from a
control that cannot fail, so each mutation here is now confirmed applied before
its result is read.

| Arm removed | Exit | Case |
| --- | ---: | --- |
| a fourth category added | 1 | `test_categories_are_exactly_the_three` |
| a consequence substituted | 1 | `test_the_six_consequences_are_exactly_the_contracted_ones` |
| a second firing test offered | 1 | `test_the_firing_paragraph_carries_no_second_predicate` |
| the firing predicate moved out of the step | 1 | `test_the_whole_firing_predicate_sits_inside_the_step` |
| `bounded spike` dropped from its destination | 1 | `test_each_destination_carries_its_contracted_semantics` |
| the design-prose exclusion dropped | 1 | `test_each_destination_carries_its_contracted_semantics` |

## Post-gates review round 2 — eight findings, all sustained (2026-09-17)

Four Blockers. Two of the four were defects **in round 1's repairs**, and one
was the repair sequence itself.

**The repairs were not projected.** Round 1's fix to the anti-pattern list landed
in `packs/core/.apm/skills/new-spec/SKILL.md` after `make build-self` had already
run, so `.claude/` and `.agents/` both still carried "the one check you
attempted" — and this ledger claimed parity. Two runtime surfaces were shipping
the text the repair removed. Projections are regenerated last now, after the
final source edit, and the old phrase returns no match anywhere under `packs/`,
`.claude/` or `.agents/`. Parity is recorded as the check rather than as a value: `catalogue self-host
--check` returns ok. See § "Why no digest value is recorded here".

**Both pointers had broadened the rule while removing its bound.** Round 1's fix
to the guide deleted the destination paraphrase and left "a candidate it cannot
settle is routed" — dropping the load-bearing bound, so the pointer described a
wider rule than the one it points at. `work-loop`'s pointer had the same defect.
Both now name the bound and repeat neither it nor the destinations in full.

| # | Defect | Confirmed by |
| --- | --- | --- |
| 1 | round 1's repair absent from both projections | reading the projected files |
| 2 | both pointers dropped the load-bearing bound | reading them against the firing predicate |
| 3 | the taxonomy regex saw only single-word labels | mutation — `**Customer impact** —` stayed green |
| 4 | counting `fires only on` misses a differently-worded second predicate | reading the arm against AC-0004 |
| 5 | the eval's expected output restored the one-check count and forbade a probe the step permits | reading it against the shipped step |
| 6 | the task-local observation was still overstated, at four fields | reading `T1`'s `Tests` again |
| 7 | a stale test name and a stale 203 count in this file | reading it against the suite |
| 8 | the five task fields were attributed to AC-0007, not AC-0006 | reading the criteria |

**Finding 6 is the fourth draft of one admission.** The first called the
task-local routing a clean example; then four of five fields; then two; it is
three. Round 3 found the verification mode that round 2's correction had
dropped — the two corrections erred in opposite directions, which is why the
sequence is recorded rather than only its result. "Compute it from `git show HEAD:`" is a procedure for
obtaining a value, not a predicate that settles an open question, and no
verification mode is stated for that bullet. Each draft was written to correct
the last and each still over-counted in the same direction.

**Finding 4 marks where a control stops reaching.** No pattern decides whether
an arbitrary added sentence is a second firing test. The arm pins the firing
paragraph's sentence count at three instead, so an inserted predicate reddens it
while it claims nothing about recognising one by wording. Proved: adding "The
rule also applies whenever you feel unsure." reddens
`test_the_firing_paragraph_carries_no_second_predicate`.

| Arm removed | Exit | Case |
| --- | ---: | --- |
| a multi-word fourth category added | 1 | `test_categories_are_exactly_the_three` |
| a second predicate added to the firing paragraph | 1 | `test_the_firing_paragraph_carries_no_second_predicate` |

## Post-gates review round 3 — five findings, all sustained (2026-09-17)

Three Blockers. Two were defects introduced by round 2's repairs, and one was a
surface no criterion can reach.

**The sentence pin was counting three where the prose has four.** `cost.**`
blocks a space-anchored split, so the raw count merged the bold lead with the
sentence after it. The pin held and reddened correctly, but its assertion
message said "three sentences" about a four-sentence paragraph — a control whose
number is right for the wrong reason, and whose stated reason was false.
Markdown is stripped before counting now.

**Round 2's pointer repair created a contract violation.** Round 2 found both
pointers had dropped the load-bearing bound and broadened the rule; the repair
added the bound back, which the *Always do* boundary forbids — a pointer carries
the anchor "and none of its content", and a paraphrased firing bound is content.
Both repairs were wrong in opposite directions. Neither pointer now characterises
when the rule fires or where a claim goes; each says the assumptions step owns
both and names the anchor. That satisfies the boundary without broadening the
rule, and needed no amendment.

**The changelog had become an untested second home.** Its highlight restated all
three destinations. AC-0001 scans `packs/core/.apm/skills` and `guides`, so
`docs/product/changelog.md` is outside the swept set and no control could see it.
Rewritten to state the effect an adopter notices and point at the one home. The
gap is real and recorded: a second home in a file outside those two roots is
invisible to the criterion.

**`make build-self` refused a dirty tree, and the refusal was load-bearing.**
`self-host: working tree is dirty — refusing to write.` The first attempt to
re-project after these repairs did nothing, and the `work-loop` projection stayed
at its previous value while its source had already moved — the same
stale-projection defect round 2 had just found, arriving a second time by a
different route. Projection is now: commit, project, commit, then
`self-host --check`. All six copies agree and the check returns ok.

**A third and fourth correction to one count.** The task-local field count read
four, then two, and is **three**: `spec.md` § Testing Strategy declares every
criterion goal-based, which supplies the verification mode round 2's correction
had dropped. The two corrections erred in opposite directions.

| # | Defect | Confirmed by |
| --- | --- | --- |
| 1 | the sentence pin counted three where the prose has four | measured both splits |
| 2 | round 2's pointer repair violated the single-home boundary | reading it against *Always do* |
| 3 | the changelog restated all three destinations, outside AC-0001's roots | reading the swept set |
| 4 | the field count was two, and is three | reading `spec.md` § Testing Strategy |
| 5 | a stale test name, a stale gate count, and a T4 digest snapshot presented as final | reading this file against the tree |

## Post-gates review round 4 — seven findings, all sustained (2026-09-17)

Two Blockers, and both were the **second** failure on the same repair.

**The `work-loop` pointer still carried routing content.** Round 3's repair
removed the firing bound and left "Reaching an approved spec does not discharge
it — a claim the contract now rests on is already past the gate the routing
exists to protect." That is a statement about resolution timing, which is
content, while the sentence beside it claimed to state none. The pointer is now
one clause: the assumptions step owns it, under the anchor. Third attempt at one
sentence.

**The changelog was still a second home.** Round 3's rewrite removed the
destination list and kept the discriminator ("what being wrong about them would
cost you"), two of the three routes, the cardinality removal, the sweep bound,
and an unmeasured behavioural claim — "the effect you notice is that fewer
questions survive into an approved spec" — which this spec's own Follow-ons
forbid claiming. Rewritten to the capability and a pointer carrying the literal
anchor. Second attempt.

**Five stale numbers, each now measured rather than typed.** The body count was
735 and is **734** — 745 file lines less an 11-line frontmatter. A mutation row
named `test_no_alternative_firing_test_is_offered`, which round 2 replaced. A
heading still read four of five where the analysis beneath it read three. The
digest pointer called round 2's `work-loop` value current, though round 3 had
moved it. And the over-firing check said "eleven Technical entries" where the
spec has **eight Technical and three Process**, eleven in total.

Every number in this file was recomputed from the tree for this round rather than
edited in place. The recurring defect across all four rounds is the same one this
delivery's own rule addresses: a claim written from what the author meant rather
than from what the artifact says.

| # | Defect | Confirmed by |
| --- | --- | --- |
| 1 | the `work-loop` pointer carried resolution timing | reading it against *Always do* |
| 2 | the changelog carried the discriminator, two routes, and an unmeasured effect claim | reading it against the boundary and Follow-ons |
| 3 | body count 735, measured 734 | recomputing the linter's slice |
| 4 | a mutation row named a replaced test | reading the suite |
| 5 | a heading read four of five over an analysis reading three | reading both |
| 6 | the digest pointer cited a superseded round-2 value | reading the round-3 entry |
| 7 | eleven Technical entries, measured eight | counting the spec's Assumptions |

**Mutation record re-taken after a lint-driven edit.** `lint-ruff` required two
rewrites in the suite (SIM300, C416) and a docstring escape fix (W605). Three
arms were re-proved against the edited code rather than left on the pre-edit
record: the row-keys arm, the duplicate-row arm, and the second-home arm.

### Gates

Re-measured after the round-5 repairs, which is the only run this line reports;
every earlier round's figures stay in that round's own entry:
`lint-ruff` 0, `lint-mypy` 0 over 148 source files,
`packs/core/tests/skills/new-spec/` 204 passed with 29 subtests, and
`catalogue self-host --check` ok. Earlier rounds' figures are not carried
forward; each round's own entry states what it measured.

## T3 — the shipped rule against this delivery's own claims (2026-09-17)

Visual / manual QA. The artifact is guidance an agent reads, so the documented
happy path is a real authoring pass. Three claims from this delivery's own
authoring were routed by the shipped table. Each routing is recorded with what
actually happened to that claim, including where the outcome was bad.

**1. `reaches-the-contract` — and this one is the rule's own case against the
delivery that wrote it.** The claim: *each sampled delivery's `plan.md` records
an owner-approval line.* Its falsehood changes the discriminator that decides
which evidence shapes earn an obligation, which decides which acceptance
criteria exist. That is a criterion and a chosen mechanism, so the table routes
it to a bounded spike **before approval**. What happened instead: the claim went
unexamined into the round-3 discriminator, and round 4 established that no
`plan.md` in the sample carries such a line. The discriminator was withdrawn,
two evidence shapes were cut on a test that had never been applicable, and the
scope of the delivery changed after four review rounds. The spike the rule asks
for is one `grep` over five files. Recorded because the rule firing correctly on
its own author's mistake is the strongest evidence available that it fires at
all, and the weakest possible claim that the author was already doing it.

**2. `unstarted-task-method` — routed to the right destination, and three of its
five fields, which means the plan did not satisfy it.** The claim: *step 5a's
protected region can be pinned by a digest.* The digest value was unknowable at
approval, so `T1`'s `Tests` named **three** of the five fields: a
constraint (byte equality), a required outcome (the heading, firing condition
and probe bound unchanged), and a verification mode — `spec.md` § Testing
Strategy declares every criterion goal-based, which supplies it. Missing: the
discovery predicate and the kill condition. "Compute it from
`git show HEAD:`" is a procedure for obtaining the value, not a predicate that
settles the open question. So
this is not the clean example the first draft of this ledger called it. The
count then read four of five, then two of five, and is three: the plan reached
the right destination and filled three of its five fields, which is a finding against the
plan rather than evidence that the rule was already being followed.
The missing field would have read: abandon the digest pin if step 5a's text is
itself amended under A4, since the pin would then be asserting a superseded
baseline. It resolved during T1, the value is in the suite
rather than here, and the arm reddens on a one-word edit. This is what the
destination looks like when it works, and the plan reached it without the rule.

**3. `cheap-with-an-oracle` — settled by a test in under a minute.** The claim:
*`parents[4]` is the repository root from the suite's location.* It is
`packs/`; the root is `parents[5]`. Twenty of twenty-two cases failed on the
first run and named the cause. The rule routes this away from design prose, and
that routing is right: a pre-approval spike for it would have been wasted work,
and no design document would have caught it. The same is true of the vacuous
uniqueness anchor above, which only a mutation could find.

**Over-firing check.** Every ordinary fact in the spec's Assumptions was
re-read against the consequence test. None of the eleven entries — eight Technical, three Process — moves
any of the six named consequences — they record probes whose results the contract
does not turn on — so the rule reaches none of them and demanded nothing. One
candidate was ambiguous: *the core release surface is three files.* It was
verified by probe rather than routed, and its falsehood would have moved no
criterion, only `T4`'s file list. Recorded as the closest call rather than as a
clean result.

## T3 — the eval register entry is executed by nothing (2026-09-17)

One output eval is added to `new-spec`'s register. It is documentation, not
coverage, and the reason is mechanical rather than a matter of degree:
`agentbundle pack evals run` selects its check with `--check`, whose
`choices=("activation", "behavior")` default to `activation`
(`pack_evals.py:1143-1148`); `.github/workflows/pack-evals.yml:68` passes
neither `--mode` nor `--check`; so the defaults select headless activation,
which reads `evals/eval_queries.json`. Nothing in that workflow opens
`evals/evals.json`. A regression deleting the routing rule still passes every
workflow; the structural suite above is what catches it.

An earlier draft of the spec said this entry was "real coverage but never a
gate", and named `--mode` as the flag. Both were wrong — the flag is `--check`,
and the entry is not coverage at all. The no-coverage conclusion the wrong flag
name supported happened to be right, which is exactly why the flag was worth
checking rather than asserting.

## T4 — the release surface is three files (2026-09-17)

`packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` both move
2.26.11 → 2.26.12, with a `## [core][2.26.12] — 2026-09-17` entry directly
beneath `[Unreleased]`. `core` carries no entry in
`.claude-plugin/marketplace.json`, so there is no fourth file.

Projections were regenerated through `make build-self`, never hand-edited.
The digests recorded at T4 were a **snapshot of that wave**,
and both moved when the review rounds edited the source. Recording the value at all was the mistake, not
recording a stale one: see § "Why no digest value is recorded here".
`self-host --check` is re-run after every source edit rather than once at T4. Recording the snapshot as final was the
mistake that let round 1's repair ship unprojected.

## Process deviations, recorded rather than absorbed (2026-09-17)

**No implementer subagent was dispatched.** `loop-cohort schedule` emitted four
single-task waves and an `implementer` is installed, so the contract asked for
one dispatch per task. All four were executed by the controller instead. The
work was prose surgery on a skill plus the suite that pins its structure, where
the review history was the asset; that is a reason and not an authorization, so
the degradation is recorded here.

**Three `wave-passed` transitions were chained with their cohort advances, and
the engine refused all three.** `wave-passed` is illegal from
`CODE-IMPLEMENTATION` — the legal route is `wave-complete` to
`CODE-VERIFICATION` first — but `wave advance` had already been chained behind
each attempt on the same command line, so the cohort pointer moved 0 → 3 while
the engine recorded nothing. Checked afterwards rather than assumed: the engine
is unchanged at `transition_sequence: 13` with `last_event: plan-locked`, so no
sequence was consumed and no round is duplicated; the cohort reports
`wave_index=3 is the last wave (total=4)`.

**What was skipped, stated rather than glossed.** Waves 1, 2 and 3 never ran
their own `wave-complete` → per-wave gate → `wave-passed` cycle. All four tasks
were implemented before any gate ran, and the gates that then ran were
cumulative over the whole change. Cumulative gates cannot reconstruct three
per-wave verifications: they cannot show that T1 left the repository green
before T2 began, which is the property the per-wave cycle exists to establish.
The final state is coherent and the change is green, and neither of those is
the same as the wave protocol having been followed. The rail exists for exactly
this: never put an engine transition and its cohort advance on one line,
because the second runs whether or not the first was accepted.

## Post-gates review round 5 — four findings, all sustained (2026-09-17)

Two Blockers, both the **third** failure on one sentence and the **third** on
one changelog entry.

**The `work-loop` pointer, attempt four.** Round 5 found that "A claim this step
cannot settle" is itself a firing condition — and an overbroad one, since the
shipped rule fires only on a load-bearing claim — while "is not resolved here"
states timing. Both are content the *Always do* boundary keeps in one home. The
pointer is now a single clause naming the owner and the anchor and nothing else.
Four attempts: paraphrase the destinations, drop the bound and broaden, restore
the bound and violate the boundary, then state only ownership.

**The changelog entry, attempt three.** "A spec no longer freezes on a question
nobody answered" is a behavioural claim, which this spec's Follow-ons route to
`guidance-activation-measurement` and forbid claiming here; the second highlight
still described the removed fixed count and its bound. The title now names the
capability and the cardinality bullet is gone.

**Three digest values survived the round-4 removal**, including one in the very
section declaring that none is recorded. Zero remain.

**The gate receipt named round 3 while sitting after round 4's repairs.** Each
round's figures now stay in that round's entry and the standing receipt names the
run it measured.

| # | Defect | Confirmed by |
| --- | --- | --- |
| 1 | the pointer's two surviving clauses were a firing condition and a timing claim | reading it against *Always do* |
| 2 | the changelog title claimed an effect and a bullet restated the cardinality | reading it against Follow-ons |
| 3 | three digest values survived, one inside the no-value section | grep for a truncated digest |
| 4 | the standing gate receipt named a superseded round | reading it against the entries below it |

## Post-gates review round 6 — one finding, and it was the shipped rule (2026-09-17)

The round was briefed to weight shipped artifacts over log prose, after three
rounds dominated by ledger wording. It returned one Blocker, in the rule itself.

**The routing table was not total over its own firing predicate.** The firing
predicate names six consequences. The `reaches-the-contract` row enumerated a
*different* list — intent, an acceptance criterion, architecture, a dependency
choice, a security or data boundary, the task graph, a verification mechanism —
which omitted two of the six: the **consequential failure direction** and the
**chosen mechanism**. A claim that fired the rule through either matched no
routing input and had nowhere to go. Neither the criteria nor any control
forbade that: AC-0006 requires the table total over its own row keys, which it
was, and nothing tied the row keys back to the predicate's domain.

Repaired by construction rather than by extending the list. The row now reads
"any of the six above, unless a row below applies. This is the residual route,
so no load-bearing claim is unrouted." A residual route cannot leave a
consequence unmapped, and the second enumeration — which was itself a second
home for the six, free to drift — is gone.
`test_the_table_is_total_over_the_firing_predicate` asserts the residual wording
and that the row does *not* restate the consequences.

| Arm removed | Exit | Case |
| --- | ---: | --- |
| residual route replaced by a partial list | 1 | `test_the_table_is_total_over_the_firing_predicate` |
| the residual-route guarantee removed | 1 | `test_the_table_is_total_over_the_firing_predicate` |

**What this says about the five rounds before it.** Rounds 3, 4 and 5 found
fifteen defects between them and thirteen were prose in this file. The one
substantive defect in the shipped rule surfaced only once the brief said to
weight shipped artifacts above log wording. The review was finding what it was
pointed at, and for three rounds it was pointed at the cheapest surface.

## Post-gates review round 7 — two findings, both in the shipped rule (2026-09-17)

**The two exception routes overlapped.** An unstarted task's helper, fixture or
symbol choice can also be a cheap reversible detail a test decides directly, so
both rows matched and prescribed conflicting destinations. Round 6 had made the
table total and left it non-disjoint. `unstarted-task-method` now carries the
discriminator — "and no test can decide it directly" — which is the exact
negation of `cheap-with-an-oracle`'s **direct-test** conjunct, not of its whole
cheap-and-reversible condition. That is enough for disjointness, because no
claim can both admit and not admit a direct test, and the table states once that
exactly one row applies. Disjointness is now a property of the wording rather
than of the reader's judgement.

**The totality arm did not assert the clause it depended on.** Deleting
"so no load-bearing claim is unrouted" left the arm green, because it checked
the label "residual route" beside the guarantee instead of the guarantee. It
also exempted `boundary` from the no-restatement loop, which permitted a partial
predicate restatement. Both closed: the guarantee clause is asserted directly,
and the loop now runs over the predicate's own article-bearing forms with no
member exempted.

| Arm removed | Exit | Case |
| --- | ---: | --- |
| the guarantee clause alone | 1 | `test_the_table_is_total_over_the_firing_predicate` |
| the residual route replaced by a predicate restatement | 1 | `test_the_table_is_total_over_the_firing_predicate` |
| the exception-route discriminator | 1 | `test_the_two_exception_routes_are_disjoint` |
| the exactly-one-row statement | 1 | `test_the_two_exception_routes_are_disjoint` |

Both findings were consequences of round 6's repair, which is the pattern this
delivery has shown at every stage: the repair is the likeliest source of the next
defect. Round 6 made the table total and introduced an overlap; its control
asserted the label and not the clause.

## Post-gates rounds 8 and 9, and the quality pass (2026-09-17)

Round 8 returned one Nit — the ledger called the exception discriminator a full
negation of `cheap-with-an-oracle` where it negates only that row's direct-test
conjunct — and confirmed the shipped routes disjoint. Round 9 confirmed the
repair: `Clean — ready to commit.`

**Nine adversarial rounds: 10, 8, 5, 7, 4, 1, 2, 1, 0 findings. Every one
sustained; none refuted.**

### The quality pass — five Concerns, two fixed, one message repaired, two recorded

Run on `gpt-5.6-terra` with a testability, observability and maintainability
lens. Its subject was the **cost of living with** what the adversarial rounds
made correct, and it found things nine correctness rounds had no reason to look
for.

**Fixed — `cheap-with-an-oracle` left "reversible" to the author's judgement.**
The row now defines it: undoing it needs no migration, no external side effect,
and no change to a user-visible contract. Where a claim lands changed on a word
the rule never defined, which is the kind of ambiguity that produces two authors
routing the same claim two ways.

**Message repaired, control kept — the four-sentence pin and the step-5a
digest.** Both are real maintenance costs and the pass was right that each
failed with no repair path. Neither is removed: the sentence count is the only
available proxy for AC-0004's "no alternative test" half, and the digest is what
AC-0007 makes contractual because step 5a belongs to slice A4. Both failure
messages now say what the arm stands in for, what to do if the edit was
deliberate, and what to do if it was not — including where to recover step 5a's
text.

**Accepted as proportionate — the five-entry cut fixture encodes delivery
history.** The pass is right that AC-0008 pins what was decided rather than an
enduring property of the rule. That is the criterion's purpose and the owner
approved it: five shapes were cut across four rounds and an extended sample, and
a cut held only by a changelog entry comes back. The maintenance cost is real
and accepted; changing it needs an amendment, not a repair.

**Bounded out of scope — noncompliance is invisible.** A spec can misroute a
claim and nothing records it. This is true, already stated in `spec.md` §
Testing Strategy, which gates nothing on the behavioural property, and its owner
is `docs/product/briefs/guidance-activation-measurement.md`. The pass's remedy —
a route-and-rationale entry in every generated spec — is a new template
obligation and a larger change than this slice; it is named for that owner
rather than absorbed here.

## Rebase onto main, four conflicts and one silent collision (2026-09-17)

Main moved two commits ahead: `6d89b39ce` and `ecba88748`. Rebased with
`rerere` **disabled** for the run, because the shared git directory holds 458
cached resolutions and this repository has a recorded instance of `rerere`
replaying a peer's resolution and silently discarding a version bump. Every
conflict below was resolved by hand.

**The version collision did not conflict, which is why it was the dangerous
one.** Main released `core 2.26.12` while this branch carried its own bump to
2.26.12. Both sides wrote the same bytes, so git auto-merged `pack.toml` and
`plugin.json` with no marker. Found by comparing the merge base (2.26.11),
main (2.26.12) and this branch, not by reading the conflict list. Now 2.26.13 in
both files with a matching changelog heading — the next patch above main, which
is what the delivery-contract suite requires.

**The changelog conflict was inside main's released section.** Both sides had
written under `## [core][2.26.12]`. Main's content stays there; this change's
content became a free-standing `## [core][2.26.13]` directly beneath
`[Unreleased]`, newest first, with one blank line above and below every
heading.

**`evals.json` was rebuilt from both parents rather than spliced.** Main added
`a-partial-lint-rule-is-un-run-not-clean`; this branch added
`load-bearing-claim-routing-by-consequence`. Seventeen entries, ids asserted
unique, the JSON re-parsed.

**One captured observation was dropped as a duplicate of an active topic.** The
knowledge journals are event logs — `observation.captured` then
`observation.dispositioned`, unique on the pair, not on `capture_id`; a first
resolution attempt asserted uniqueness on `capture_id` alone and failed against
main's six dispositioned captures. The antipattern journal took main's twelve
events plus this delivery's one pending capture. The pattern journal took main's
twelve only: this delivery's review-attention lesson duplicates
`a-review-rounds-findings-measure-where-its-brief-pointed`, which main distilled
on 2026-09-11 from `docs/specs/acceptance-criteria-set-construction/plan.md` —
before this delivery began. Keeping it pending would have invited a second topic
for one lesson. The recurrence is still worth recording; doing it means adding
an occurrence to that existing topic, which is a distil-time mutation and not a
rebase decision.

**`workspace.toml` auto-merged and was checked anyway**, because a merge here has
resurrected retired register entries before. Compared semantically against main:
`[backlog].open` is 151 entries on both sides with nothing added or removed, and
the only difference is this delivery's own `ini-002` active entry.

**Main's rule 9 now runs against this spec.** `ecba88748` made
`lint-contract-item-alignment.py` resolve its own base revision, so the
stale-assertion rule no longer reports as partial for want of `--since`. Run
against this spec directory post-rebase: 0 findings, and no rule reports missing
input. Gates on the new base: `lint-ruff` 0, `lint-mypy` 0 over 148 files,
`packs/core/tests/skills/new-spec/` **221 passed** with 35 subtests — up from 206
because main added cases — and `catalogue self-host --check` ok.

## Two CI gates failed that no local run had reached (2026-09-17)

Both were gates with no pytest surface in anything this delivery ran, so nine
adversarial rounds, a quality pass and every local gate passed while the branch
was red on push. The pattern is recorded in this repository already and it
repeated here anyway.

**`lint-pack-test-boundary` — six failures.** The construction suite lived in
`packs/core/tests/` and anchored at `Path(__file__).resolve().parents[5]`, the
repository root, to reach `guides/`. A pack test may not read above
`packs/<pack>/`. The suite was genuinely repository-level in two of its arms and
pack-local in the rest, so it split along the boundary the rule enforces rather
than moving wholesale:

- the pack half stays at
  `packs/core/tests/skills/new-spec/test_load_bearing_claim_grounding.py`,
  anchored at `parents[3]` = `packs/core`, and no longer names `_REPO` at all;
- AC-0001's sweep across `guides/` and AC-0002's adopter-how-to pointer moved to
  `tests/roster/test_load_bearing_claim_routing_surfaces.py`, anchored at
  `parents[2]` = the repository root.

Each file states in its docstring which criteria the other owns, so neither
silently covers the other's arms.

**Landing in `tests/roster/` was only half the move.** `make test` collects it,
so a green local run proves nothing about CI — CI does not auto-discover roster
tests. A named step was added to `build-check.yml` with the reason in a comment,
following the RFC-0099 step's precedent, plus a `STEP_DISPOSITION` entry in
`tools/lint-ci-parity.py` keyed on that exact step name. Verified rather than
assumed: `lint-ci-parity` reports 95 steps, all dispositioned.

**`PackSkillPytestShapeTest` — one failure.** A pack skill test may not carry an
`if __name__ == "__main__"` guard. Removed from both files; 112 of the 115
existing roster suites already omit it.

**A mutation reported GREEN and had never applied, for the third time in this
delivery.** The disjointness-discriminator probe used `sed` on a pattern
containing `**`, which failed with `RE error: repetition-operator operand
invalid` — so the file was untouched and the arm looked dead. Re-applied through
Python, it reddens. Every mutation here is confirmed applied before its result
is read, and `sed` is not the tool for a pattern carrying Markdown emphasis.

Post-fix, on the rebased base: `lint-pack-test-boundary` 8 cases pass,
`lint-ci-parity` clean on both arms, `tools/test_build_gate_chain.py` 40 passed
with 28 subtests, `lint-ruff` 0, `lint-mypy` 0 over 148 files, and the two split
suites 24 passed with 35 subtests. Five mutations across both files redden.

## Two more gates no local run reached, and one failure that is not this change (2026-09-17)

**`test_protected_manifest_covers_every_literal_roster_spec_dependency`.** The
new roster suite names `docs/specs/load-bearing-claim-grounding/spec.md` in its
docstring, which makes the spec directory a literal roster dependency, and
`.workspace-prune-protected.toml` is re-derived from exactly those. Added in
sorted position; the manifest is 95 entries and the sort is asserted, not
assumed. A sibling delivery recorded needing the same entry and calling it
unanticipated, so this is the second instance of one class.

**`test_no_fail_closed_lifecycle_findings` — `impossible_transition`.** The spec
reached `Status: Shipped` while `workspace.toml` still listed it under
`[ini-002].work.active`. Moved to `shipped` with its comment, re-parsed to
confirm it is in exactly one bucket.

Both suites now pass: 72 passed, 12 subtests.

### `gate-sast` is red on `main`, not on this change

`audit-npm` blocks on GHSA-9rgm-9g3h-6x36, a moderate DoS advisory in `devalue`,
in `docs-site` and `web`. Attribution measured rather than assumed: this branch
changes **zero** `package.json` or `package-lock.json` files, and `main`'s own
`build-check` run on `f443b09ff` — the commit this branch is rebased onto —
failed at 2026-09-17T22:19 while `6d89b39ce` and `ecba88748` were green at 20:47
and 20:35. The advisory landed upstream in that window.

Fixed anyway, as a **Tier-1 bundled fix**, because `gate-sast` is a required
check and the alternative is a branch that cannot merge behind a break it did
not cause. Command: `npm audit fix --package-lock-only` in each project. It
moves `devalue` 5.8.2 → 5.9.2 in `docs-site` and 5.8.1 → 5.9.2 in `web` — six
lines each, one transitive dependency, no direct-dependency or manifest change.
Re-run produces a **zero diff**, and `audit-npm` then reports no blocking
advisories in either project at `--audit-level=moderate`.

## Why no digest value is recorded here (2026-09-17)

Four rounds produced four digest values for `work-loop/SKILL.md`, each one
recorded as current and each invalidated by the next round's edit to the file
it described. The last instance was self-inflicted in the same entry that
complained about the previous one: round 4's write named a value that round 4's
own pointer repair had already moved.

A digest of a file under active review is a claim with a guaranteed expiry, and
no amount of care in restating it changes that. So this ledger records **the
check, not the value**: `agentbundle catalogue self-host --check` compares the
pack sources against `.claude/` and `.agents/` and returns ok, and it is re-run
after every source edit. The sequence that makes it meaningful is
commit → `make build-self` → commit → check, because `build-self` refuses a
dirty tree and does nothing if the tree is not clean.

This is the one repair in this delivery aimed at the generator rather than an
instance, and it is recorded because the four preceding attempts were all
instance repairs that each produced the next defect.
