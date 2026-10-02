# Proposal: narrow the review-effectiveness study to a question it can answer

- **Status:** Draft, awaiting owner approval and independent review
- **Raised by:** the study controller, 2026-10-02
- **Decides:** whether to amend `immutable_contract` in
  [`review-effectiveness-baseline.json`](review-effectiveness-baseline.json) to
  a narrower question, or to run the frozen eight-case plan to the window close
  and report incomplete
- **Deciders:** the owner **and** independent review, together. The controller
  cannot do this alone and has not.

## What is being asked

The study's frozen contract asks: **does adversarial review find defects that a
cold audit would not?** Answering it needs 8 terminal cases, each with a shadow
audit to compare against.

This proposal says that question is **not reachable** under the frozen limits,
shows the arithmetic, and offers two narrower questions the evidence in hand
already nearly answers. It changes nothing by itself.

## The frozen question cannot be answered under the frozen ceilings

This is the decisive point, and it is arithmetic rather than judgement.

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

**Option A — amend to a narrower question.** Pick one of:

- *the adjudicator's refusal rate and what it protects.* Four cases suffice. The
  measurement is already collected as a by-product of every round, needs **no
  shadow audit**, and therefore does not touch the input-token ceiling at all.
- *the repair-origin rate and what turns it.* Also four cases, also no shadow
  audit — but it needs `repair_origin_findings` recorded per round on every
  case, which case 3 shows is easy to skip.

Either reaches a reading inside the window. Both answer a question the study did
not set out to ask.

**Option B — keep the frozen contract.** Admit toward 8, accept that the shadow
comparison stops at about three cases, and report incomplete on 2026-10-29. Zero
governance cost. The frozen question stays unanswered.

**Option C — amend the ceilings only, keeping the question.** Needs a ceiling of
at least 6,775,344 returned input tokens, a 2.35× rise, justified by n=1. The
controller recommends against it: a frozen parameter should not move that far on
one observation.

**Recommendation: Option A with the adjudicator question.** It is the only
option that produces a defensible reading inside the window, it rests on data
already being collected, and it avoids the shadow audit entirely — which is
where the whole budget problem lives.

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
