# Proposal: the review-effectiveness study cannot answer its frozen question

- **Status:** Draft, awaiting owner approval and independent review
- **Raised by:** the study controller, 2026-10-02
- **Decides:** what to do about three independent blockers that make the frozen
  question unreachable — stop and write up what is counted, re-charter the
  measurement contracts in
  [`review-effectiveness-baseline.json`](review-effectiveness-baseline.json), or
  run to the window close and report incomplete
- **Recommends:** stop admitting and write up the three counted observations
  (Option D)
- **Deciders:** the owner **and** independent review, together. The controller
  cannot do this alone and has not.

## What is being asked

The study's frozen contract asks: **does adversarial review find defects that a
cold audit would not?** Answering it needs 8 terminal cases, each with a shadow
audit to compare against.

This proposal shows that the question is **not reachable**, for three
independent reasons, and asks the deciders to choose what to do instead. It
changes nothing by itself.

| Blocker | What fails | Fixable by narrowing the question? |
| --- | --- | --- |
| **A** | 8 shadow audits need 2.35x the frozen cohort token ceiling | Yes — a question needing no shadow audit avoids it |
| **B** | 0 finding rows exist against a >= 0.80 lineage-completeness threshold | **No** |
| **C** | Normal-loop input/output tokens and all prose-churn attribution were never captured | **No** |

Blockers B and C were found while checking a claim this document made in its
own first draft, and they apply retroactively to the three admitted cases. They
are the reason the recommendation changed.

## Blocker A: the frozen question cannot be afforded

This is arithmetic rather than judgement.

One shadow audit start consumed **846,918** returned input tokens. The cohort
ceiling is **2,880,000**. Eight cases need eight shadow starts:

| Quantity | Value |
| --- | ---: |
| Observed cost of shadow start 1 | 846,918 |
| Eight shadow starts at that rate | 6,775,344 |
| Frozen cohort ceiling | 2,880,000 |
| Overrun | **2.35×** |

The ceiling supports about **three** shadow audits. The comparison needs eight.
No amount of remaining calendar time changes this, and the two levers that look
like escapes both fail:

- **Narrowing the shadow's read surface** would cut per-start cost without any
  amendment. It also breaks the comparison: the normal loop's reviewers read the
  repository freely, so a read-restricted shadow is no longer measuring the same
  activity. This trades the study's validity for its budget.
- **Redefining `returned_input_tokens`** to count uncached input only was
  considered on 2026-09-30 and declined, because choosing a measurement
  definition to make the result convenient is the bias this contract bans.
  Raising a ceiling for the same reason is the same move with a different lever.

So the honest status quo is: run to 2026-10-29 and **report incomplete**. That is
the contract working as designed, not failing.

## Two further blockers, found after this proposal was first drafted

The controller checked its own claim that the narrower questions are "already
collected as a by-product of every round". **That claim was wrong.** Checking it
found two more blockers, both independent of the token ceiling and **neither
solved by narrowing the question.**

### Blocker B: no finding rows exist

`lineage_completeness_contract` requires **one finding row of 24 fields for
every finding** emitted by normal review, closure review, shadow audit or
adjudication, and sets a cohort threshold of **>= 0.80** complete fields across
case rows and finding rows together.

| Quantity | Value |
| --- | ---: |
| Raw findings tallied across the 3 admitted cases | ~289 |
| Finding-row field values those would require | ~6,936 |
| **Populated finding rows in the ledger** | **0** |
| Case-row field values required (3 x 19) | 57 |
| Case-row field values actually present (3 x 2) | 6 |
| Cohort completeness | **~0.001** against a 0.80 threshold |

The ~289 is a rough lower bound from the ledger's own per-round tallies and may
double-count where a round is recorded twice. The exact figure does not matter:
the numerator is 0 finding rows, so no plausible count reaches 0.80.

The ledger records findings as **per-round aggregate counts and prose notes**
instead — raw, sustained, refuted, blockers. Those are genuinely useful and are
what every observation in this study rests on. They are not what the contract
requires, and the gap is not a naming mismatch.

### Blocker C: normal-loop cost was never split into input and output

`cost_telemetry_sufficiency` requires normal-loop **input** tokens and **output**
tokens separately, plus prose-churn-attributable actions, input tokens, output
tokens and wall time **for every prose_churn event**.

- Case 4 carries **19** undifferentiated `returned_subagent_tokens` totals and
  **zero** input-token or output-token fields. Cases 2 and 3 are the same; the
  only input/output splits anywhere belong to case 2's *shadow* pre-launch
  gates, not to any normal loop.
- **No case row carries a single `prose_churn` field.** The
  `prose_churn_missing_rule` is explicit: any `null_unknown` or
  `null_unavailable` attributable action, token or wall-time figure makes
  prospective effectiveness incomplete. Six of the 18 frozen `scorecard_fields`
  are prose-churn figures.

### Why this changes the recommendation

Both blockers apply **retroactively to cases 2, 3 and 4**, which are already
terminal. Their findings were never rowed and their per-finding and
prose-churn telemetry was never captured while the work ran. It is
session-local and gone, and backfilling it by estimation is barred.

So **no narrowing of the question alone reaches a compliant reading**, because
the lineage and cost contracts stay frozen as they are and the existing cases
fail them regardless of which question is asked. An amendment that narrows only
the question lands on `report incomplete` by a different route.

This correction cuts directly against the controller's first recommendation in
this document, which said four cases would suffice because the data was already
being collected. It was not being collected.

## The cost and the runway

Case 4 is the first case with complete per-start telemetry, so it is the only
sound basis for a per-case estimate.

| Phase | Starts | Returned subagent tokens | Wall clock |
| --- | ---: | ---: | ---: |
| Pre-EXECUTE review (7 rounds) | 15 | 1,142,006 | 4,106.4 s |
| EXECUTE (8 tasks, 5 waves) | 8 | 549,639 | 4,389.0 s |
| Post-gates rounds 1–2 | 12 | 878,758 | not totalled |
| **Recorded subtotal** | **35** | **2,570,403** | **8,495.4 s** = 2 h 21 m |

Post-gates round 3, the gate transitions and the controller's own verification
runs sit outside that subtotal. The whole case ran to roughly 45 starts and
2.9M tokens.

Five more cases at case 4's recorded rate is **175 starts and 12,852,015
tokens**, inside the **27 days** from 2026-10-02 to the window close on
2026-10-29 — about one case every 5.4 days. The 2 h 21 m above is machine time
on one case; the calendar time per case has been far longer.

## A correction the owner should see before deciding

Prior handovers, and the controller's own earlier recommendation, said the
repair-origin finding was **replicated across two cases and roughly 23 rounds**.
Checked against the ledger's own fields, that claim is **stronger than the
record supports**.

- **Case 4 counts it per round.** Rounds 2–7 sustained 21 findings, of which
  **16 were repair-origin** — 76%. The per-round series is
  7, 4, 2, 2, 1, 0 against sustained 8, 6, 4, 2, 1, 0.
- **Case 3 does not.** Its post-amendment rounds 2–6, the rounds the dominance
  claim is about, carry **no `repair_origin_findings` field at all**. The claim
  rests on a prose statement. Case 3's only rounds that *are* counted are its
  pre-amendment rounds 2, 3 and 4: **2, 2 and 3** repair-origin against
  sustained **15, 10 and 11** — 7 of 36, or 19%, which is not dominance.

So repair-origin dominance is **numerically evidenced on one case**, and
supported on the second by prose whose numbers were never recorded. It remains
the study's most interesting observation. It is not yet a replicated result, and
a proposal resting on "replicated" would be resting on an unchecked number —
the exact failure this study keeps recording about its own controller.

This correction cuts against the controller's earlier recommendation and is
stated here rather than quietly dropped.

## What the evidence does support

Two observations are fully counted and need no further cases.

1. **The adjudicator refuses most of what reviewers raise, and that is load
   bearing.** Case 4's post-gates rounds 1–2 produced **31 raw findings** of
   which **9 sustained** — **22 refused**. Of one counted set of 13 refusals, 4
   broke on authority, 5 on consequence, 2 on existing handling and 2 on
   observation. Twice a refusal prevented a repair that would have reintroduced
   a mechanism the spec forbids. The gateway is doing work no single reviewer
   could.
2. **One reviewer role contributed nothing on this diff.** The
   experience-reviewer raised **14 raw findings across two rounds, 1 sustained,
   0 unique** — that defect was independently found by the adversarial reviewer,
   whose duplicate the adjudicator refused. Cost: **5 starts, 272,260 tokens**.
   This is an observation on one case whose adopter surface was instruction
   prose. It is **not** a judgement about the role, and no future case may be
   selected to test it.

Review did also catch two defects in the governed work rather than in a repair,
both at case 4's round 3. The consequential one pinned a rung's `Requires` cell
by equality to a superseded value, so the contract's central edit would have
reddened a shipped assertion. Rounds 1 and 2 passed over it. That is the
clearest single piece of evidence that review surfaces what the contract alone
does not — and it is **two findings on one case**, which is why the frozen
question needs the eight-case comparison it cannot afford.

## The options

Blockers B and C rule out a question-only amendment, so the live options are
narrower than this document first claimed.

**Option A — amend the question *and* the measurement contracts.** Narrow to the
adjudicator's refusal rate, and in the same amendment replace
`lineage_completeness_contract` and `cost_telemetry_sufficiency` with what the
loop actually produces: per-round aggregate counts of raw, sustained, refuted
and indeterminate findings, with refusal grounds, and undifferentiated returned
subagent tokens plus wall time per round. Drop the per-finding rows and the
prose-churn attribution, because neither was ever captured and neither can be
recovered.

- Reaches a reading inside the window, and needs **no shadow audit**, so it
  never touches the token ceiling.
- Cases 2, 3 and 4 would count, since the amended contract asks for what their
  rows already hold.
- The honest cost: it is a **substantial** rewrite of the frozen contract, not a
  threshold tweak, and it lowers the evidentiary bar the study was designed
  around. It should be read as re-chartering the study, and the record should
  say so plainly.

**Option B — keep the frozen contract and report incomplete** on 2026-10-29.
Zero governance cost. Now the clear-eyed reading of Option B is stronger than it
was: with three independent blockers, `report incomplete` is not a near miss, it
is the only outcome the frozen contract can produce. Admitting more cases under
it buys nothing, because each new case fails blockers B and C the moment it
closes.

**Option C — amend the ceilings only, keeping the question.** Now clearly
insufficient. It needs a 2.35x ceiling rise on n=1 **and** still fails B and C.
Not recommended.

**Option D — stop admitting and write up what is actually supported.** Close
admission early, report incomplete against the frozen question, and publish the
three counted observations in their own right: the adjudicator's refusal
behaviour, the one-case repair-origin result, and the one reviewer role that
contributed nothing on one diff. No amendment, no new cases, no further token
spend.

**Recommendation: Option D, with Option A as the alternative if a formal reading
matters.** Option D is recommended because every remaining case costs ~2.5M
tokens and ~35 starts and cannot produce a compliant reading under the frozen
contract, while the observations already counted do not need one. Option A is
the right choice only if the owner wants a contract-compliant reading badly
enough to re-charter the measurement contracts, and the record should then be
explicit that the bar moved to fit what was collected — which is uncomfortably
close to the bias this contract exists to prevent, and is why it needs
independent review rather than an owner nod.

Note that stopping admission early is a **different act** from excluding case 1,
and the arithmetic that made closing admission wrong on 2026-10-02 no longer
applies the same way: that reasoning assumed the remaining cases could reach a
reading. Blockers B and C say they cannot.

## Two mechanics the deciders need to know

**The contract has no amendment path.** Its 18 top-level keys include no
`amendment_path` or equivalent. The only mechanism is
`release_contract_binding.approval_rule`: independent review and owner approval
must cite the canonical SHA-256 before `prospective_starts_authorized` can be
true. An amendment is therefore a **re-freeze and re-approval of a new
contract**, not an edit to an approved one. Both approvals currently read
`approved:d7a8e697…1bd91f`; both must be re-granted against the new digest.

**Existing case keys stay valid.** `stable_case_key` derives in part from the
canonical contract SHA-256, so cases admitted under the old digest keep keys
derived from it. That is correct and must not be recomputed. The ledger already
settled this reasoning when an accepted intent was renumbered on 2026-09-30:
enumeration-time digests record the bytes read at the time, which a later change
cannot alter, and recomputing them would produce different keys for the same
cases and fail the duplicate-or-conflict rule. Any amendment should carry the
same note.

## One more question for the deciders

The contract states its sufficiency rule two ways, and they disagree:

- `sufficiency_and_decision_rules.effectiveness_reading_requires`: "at least 8
  **terminal admitted cases**"
- `admission_rule.incomplete_rule`: "fewer than 8 admitted cases reach
  **terminal measurement**"

The frozen status list carries a distinct `measured_terminal` alongside
`normal_loop_terminal`, `shadow_terminal` and `adjudication_terminal`. If
"terminal measurement" means `measured_terminal`, then **0 of 8** are met and no
case has ever reached it. If any terminal status counts, **3 of 8** are met.
Prior handovers recorded "two are terminal", which matches neither.

This is an interpretation of frozen text, so it is not the controller's to
settle. It changes the remaining distance to a reading from 5 cases to 8, so it
should be settled in the same sitting as this proposal.

## Sign-off

| Party | Decision | Canonical digest cited | Date |
| --- | --- | --- | --- |
| Owner | | | |
| Independent review | | | |

Until both rows are filled against a new canonical digest, the frozen contract
stands unchanged and the controller continues under Option B by default.
