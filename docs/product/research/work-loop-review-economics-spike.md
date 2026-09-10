# Work-loop review economics — validation spike

Paired baseline/candidate measurement of the review stopping contract proposed by
[work-loop review economics](../intents/work-loop-review-economics.md), the first child of
[work-loop delivery efficiency](../intents/work-loop-delivery-efficiency.md).

- **Run date:** 2026-09-09
- **Owner:** eugenelim, Platform Core maintainer
- **Verdict:** recorded in [Survive/kill calculation](#survivekill-calculation) below
- **Kill condition:** predeclared 2026-09-09 in the child intent, before any case ran; not restated
  loosely here — the exact clauses are quoted in the calculation section

## What this spike tests

The riskiest assumption is that consequence-bound blocking plus focused re-review can materially
reduce both review-stage wall-clock time and model tokens without missing findings whose
consequences justify blocking delivery. The spike runs two review policies against the same six
frozen code states and compares cost and retained material coverage.

## Method amendment applied

The child intent's capture list originally required capturing the baseline arm during six future
work-loop cases. The owner authorized, on 2026-09-09, running six fresh paired baseline and
candidate sessions now against frozen completed changes instead. Corpus composition, guardrails,
and kill thresholds are unchanged. The amendment and its justification are recorded in the child
intent under "Method amendment (2026-09-09, owner-authorized)".

## Telemetry mechanism and precision

Token counts are provider-reported, never estimated from text length.

Every dispatched agent writes its own JSONL transcript to `tasks/<agentId>.output` in the session's
scratch directory. Each assistant message in that transcript carries the inference provider's own
`usage` block for the API request that produced it:

| Field | Meaning | Precision |
| --- | --- | --- |
| `message.usage.input_tokens` | uncached input tokens for that request | exact integer, provider-reported |
| `message.usage.cache_read_input_tokens` | cached input tokens read for that request | exact integer, provider-reported |
| `message.usage.cache_creation_input_tokens` | input tokens written to cache | exact integer, provider-reported |
| `message.usage.output_tokens` | output tokens, thinking tokens included | exact integer, provider-reported |
| `message.model` | the model that served the request | string |
| record `timestamp` | host clock at each record | ISO-8601, millisecond resolution |

A single agent call issues many API requests — one per reasoning or tool-use step — so a call's cost
is the sum of these blocks across the whole call. The reported figures use that per-request
transcript aggregation rather than the incomplete host summary fields described below.

**Instrument verification, and one corrected reading.** Two host summary fields look like they
already report a call total, and neither does. `toolUseResult.totalTokens` on a *synchronous* agent
result is internally consistent — across 380 historical records its four `usage` fields summed to
`totalTokens` in 380 of 380, zero mismatches — but that consistency only shows the record is
self-consistent, not that it covers the run. Checking a record against its own call proved it does
not: a `design-reviewer` call with 13 tool uses reported `cache_read_input_tokens` of 40,579, which
is roughly one request's cached read rather than the ~14 requests the call actually issued. An
*asynchronous* agent result, which is how this host dispatches agents, omits `usage` entirely; its
completion notification reports only an aggregate `subagent_tokens` with no input, cached-input, or
output split. Both fields are therefore unusable for this spike's per-class measurement, and the
per-request transcript aggregation above is used instead. The first measured call illustrates the
size of the difference: its notification reported 87,945 aggregate tokens while the provider's own
per-request records summed to 4,553,835, of which 4,315,297 were cached input reads.

**Timing precision and its limit.** Elapsed time per call is the difference between the first and
last record timestamps in that call's transcript, at millisecond resolution. On the first measured
call this agreed with the host's independently reported `duration_ms` of 443,797 to within 50 ms
(443,747 ms measured), which cross-checks the timing instrument against a second source. It is host
wall-clock, not a `CLOCK_MONOTONIC` reading; the child intent's capture list asked for monotonic
start and end times. Over call durations of minutes the difference is immaterial unless the system
clock is stepped mid-call, and no clock step occurred during the run. This substitution is recorded
as a limitation rather than silently absorbed.

## Frozen corpus

All six cases were preselected and recorded here before either arm ran on any case. No case was
replaced after its results were seen.

The **frozen pre-review revision** for each case is the last implementation commit on its pull
request's branch — the tree as it stood when implementation finished and before any review-driven
repair landed. Because these pull requests were merged with merge commits rather than squashed,
that state is a real, addressable tree, and the commits that follow it on the branch are the
historical repair record. The **review subject** is the diff from that commit's parent to that
commit. The **historical comparison evidence** is the set of branch commits after the frozen
revision, plus the governing spec's records.

| Case | Stratum | Frozen pre-review revision | Base | Review subject | Subject digest (sha256, first 16) |
| --- | --- | --- | --- | --- | --- |
| C1 | low-risk | `4a22a07ee000585fa7db3a8dccaeec064eca8ee0` (PR #1223) | `d7cf1b741` | 8 files, +17/-6 | `671ac986f1499cc7` |
| C2 | low-risk | `212b4684ff1b484781917ee42f80dac7153a7526` (PR #1214) | `2ad03c262` | 1 file, +68/-0 | `bf5aed5229b7c8e5` |
| C3 | ordinary | `8ccb191de5af274aef7991e7e1fd4cf0c4937501` (PR #1186) | `2b072b3eb` | 6 files, +92/-6 | `e82350e59be35740` |
| C4 | ordinary | `bc8f914f0dc7b192d8c25377d6f6a974551c077d` (PR #1199) | `fa9f82c4f` | 4 files, +272/-98 | `8a0749723473f732` |
| C5 | high-risk | `6f44cc462f175cd46dfa606dbae5cbdbf6985cf5` (PR #1250) | `58da5cc7c` | 5 files, +104/-2 | `309675bf14fadf5d` |
| C6 | high-risk | `5463ff3ee97c43527d2d952ba94a75092892054e` (PR #1212) | `d6b2298a1` | 2 files, +66/-29 | `44d5f586189b6737` |

### Accepted contract per case

Each contract digest is the SHA-256 of `spec.md` as it stood at that case's frozen revision, so a
later edit to the spec cannot silently change what the arms were reviewing against.

| Case | Accepted contract | Contract status at the frozen revision | Contract digest (first 16) |
| --- | --- | --- | --- |
| C1 | `docs/specs/cooling-scope-closure/spec.md` | Implementing | `254349417d7251ae` |
| C2 | `docs/specs/doc-drift-prevention/spec.md` | Shipped | `0a8af6011e4ebd21` |
| C3 | `docs/specs/project-knowledge-foundation/spec.md` | Shipped | `02c2c6e4c1dbf164` |
| C4 | `docs/specs/work-loop-review-verdicts/spec.md` | Shipped | `e5af59df958370db` |
| C5 | `docs/specs/loop-cohort-state-lock/spec.md` | Shipped | `209726711e1e368a` |
| C6 | `docs/specs/cooling-scope-closure/spec.md` | Implementing | `e096c1ef6794e320` |

### Why each case sits in its stratum

**C1 — low-risk.** `fix(core): correct the closeout comment, and give two records their evidence`.
Eight files, seventeen added lines, no protected risk class touched: the change corrects a comment
and attaches evidence to two records. It is a single bounded task with one owner and no risk
trigger, which is exactly the shape the work-loop's light mode admits. One repair commit follows it
on the branch.

**C2 — low-risk.** `test(core): catch stale core-agent projections in the roster`. One file, sixty-eight
added lines, test-only. It adds a drift guard that renders the adapter projections from current
source and compares the output. No production behavior changes, so no protected consequence is
reachable from the subject itself. One repair commit follows it.

**C3 — ordinary full-mode, single owner.** `fix(core): give a project-knowledge deadline breach its own
diagnostic`. Six files spanning a skill script, its pack manifest, and two test modules, with a
version bump. It changes user-visible refusal behavior and touches a released pack surface, so it
is beyond light mode, but it is one owner's bounded change with no destructive, migration, or
security-boundary trigger. Its branch carries a genuine review-driven functional repair —
`fix(core): stop the new deadline diagnostic being swallowed and re-refused` — which makes it a
strong test of whether the candidate arm still catches a real behavioral defect.

**C4 — ordinary full-mode, single owner.** `refactor(core): give each reviewer lens exclusive ownership`.
Four files, +272/-98, rewriting three reviewer role definitions plus a new contract test. It is a
larger reviewable surface than C3 and changes agent-facing instructions, but it introduces no
protected-class consequence and needs no migration or approval. Its branch carries a repair that
restored pinned review wording, which is the class of defect a focused re-review could plausibly
miss.

**C5 — high-risk.** `fix(core): stop a superseded reclaim from moving a live state lock`. The subject is
a concurrency fix inside the work-loop's state-lock module, with a seventy-two-line test addition
and a pack release. A wrong fix here lets one session move another session's live lock, which is a
data-loss consequence on shared state, and the defect class is a race that only manifests under
simultaneity. Three commits follow it, including a projection sync and a registered residual.

**C6 — high-risk.** `fix(core)!: consume reconciliation's cooled verdict in closeout`. The `!` marks a
breaking change to published behavior; the subject changes which verdict closeout consumes across
two engine modules. The consequence class is public-contract plus mixed-version, because a shipped
pack and its consumers disagree during rollout. Its branch carries ten follow-on commits including
a contract amendment that was later narrowed and then withdrawn, which is the richest historical
adjudication record in the corpus.

## Pinned configuration

Both arms of every case ran under one configuration. Nothing in this list changed between the first
and last case.

| Pinned item | Value |
| --- | --- |
| Host | Claude Code 2.1.266, macOS (Darwin 25.5.0) |
| Controller model | `claude-opus-5` |
| Reviewer/adjudicator model | as resolved per call and recorded in the raw measurement table |
| Reviewer-role revision | `packs/core/.apm/agents/` at working-tree revision `d44484b29` |
| Policy revision | `packs/core/.apm/skills/work-loop/` at working-tree revision `d44484b29` |
| Tool configuration | agent-definition default tools per role, unmodified |
| Contract revision | per case, digest-pinned in the table above |
| Repository under review | one disposable git worktree per case, checked out at the frozen revision |

## Arm definitions

**Baseline** is the currently installed work-loop review policy, read from
`packs/core/.apm/skills/work-loop/SKILL.md` and `references/light-mode.md` at the pinned revision:
dispatch every warranted reviewer; persist each report; route every non-clean report through
`finding-adjudicator`; repair sustained findings; then open another full round of the same reviewer
over the whole change, iterating until a round sustains nothing above a deferred Nit. Specialist
reviewers (`security-reviewer`, `quality-engineer`) fire on their own triggers.

**Candidate** is the policy the child intent proposes: one broad review; every Blocker must trace a
plausible material consequence to an accepted requirement, a protected risk class, or a repository
invariant, or it is not a Blocker; adjudicate findings; repair sustained findings; then re-review
only those findings, their fixes, the affected contract bytes, and demonstrated dependency drift.
A revision-bound result is reused while its declared subject and governing contract bytes are
unchanged.

**Arm order alternates across cases** so that any ordering advantage does not accrue to one arm:
C1, C3, C5 run baseline first; C2, C4, C6 run candidate first. Each arm runs in a separate clean
agent context with no access to the other arm's findings.

## Raw per-call measurements

Every row is one dispatched agent call. Token columns are the inference provider's own counts,
summed across that call's API requests. `Permission s` is time waiting for a human to grant a tool
permission and is excluded from the policy-attributable figure; `Load-stall s` is model or queue
wait; `Tool-exec s` is a long-running command. `Blind` rows are the independent union
adjudications and belong to neither arm.

| Case | Arm | Phase | Round | API reqs | Input | Cached in | Cache-create | Output | Total tokens | Elapsed s | Permission s | Load-stall s | Tool-exec s | Active s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | baseline | review | R1 | 75 | 150 | 4,315,297 | 210,161 | 28,227 | 4,553,835 | 444 | 0 | 0 | 0 | 444 |
| C1 | baseline | adjudication | R1 | 26 | 52 | 978,732 | 167,389 | 16,132 | 1,162,305 | 223 | 0 | 62 | 0 | 161 |
| C1 | baseline | repair | R1 | 10 | 16 | 114,557 | 51,063 | 1,536 | 167,172 | 31 | 0 | 0 | 0 | 31 |
| C1 | baseline | review | R2 | 93 | 186 | 4,960,713 | 716,766 | 40,709 | 5,718,374 | 2630 | 0 | 2051 | 0 | 579 |
| C1 | baseline | adjudication | R2 | 34 | 68 | 1,350,871 | 221,507 | 24,883 | 1,597,329 | 346 | 0 | 158 | 0 | 188 |
| C1 | baseline | repair | R2 | 33 | 41 | 766,982 | 102,786 | 9,590 | 879,399 | 191 | 0 | 75 | 0 | 116 |
| C1 | baseline | review | R3 | 76 | 152 | 5,315,600 | 212,876 | 35,286 | 5,563,914 | 549 | 0 | 0 | 0 | 549 |
| C1 | baseline | repair | R3 | 51 | 59 | 1,608,788 | 119,179 | 20,251 | 1,748,277 | 389 | 0 | 176 | 0 | 213 |
| C1 | baseline | review | R4 | 75 | 150 | 4,702,553 | 181,954 | 29,710 | 4,914,367 | 515 | 0 | 0 | 0 | 515 |
| C1 | candidate | review | R1 | 112 | 224 | 9,057,394 | 291,020 | 54,913 | 9,403,551 | 788 | 0 | 0 | 0 | 788 |
| C1 | candidate | adjudication | R1 | 34 | 68 | 1,373,433 | 149,729 | 22,363 | 1,545,593 | 311 | 0 | 0 | 0 | 311 |
| C1 | candidate | repair | R1 | 47 | 55 | 1,415,377 | 200,070 | 19,313 | 1,634,815 | 1255 | 0 | 1047 | 0 | 209 |
| C1 | candidate | re-review | R2 | 36 | 72 | 1,282,330 | 109,045 | 16,019 | 1,407,466 | 221 | 0 | 0 | 0 | 221 |
| C1 | candidate | repair | R2 | 15 | 21 | 225,200 | 45,714 | 2,790 | 273,725 | 50 | 0 | 0 | 0 | 50 |
| C1 | candidate | re-review | R3 | 27 | 54 | 942,442 | 121,663 | 19,498 | 1,083,657 | 282 | 0 | 0 | 0 | 282 |
| C2 | baseline | review | R1 | 109 | 218 | 8,842,527 | 258,441 | 42,127 | 9,143,313 | 634 | 0 | 0 | 0 | 634 |
| C2 | baseline | adjudication | R1 | 38 | 76 | 1,623,467 | 193,667 | 18,950 | 1,836,160 | 274 | 0 | 0 | 0 | 274 |
| C2 | baseline | repair | R1 | 39 | 47 | 770,435 | 162,502 | 14,377 | 947,361 | 1156 | 0 | 993 | 0 | 163 |
| C2 | baseline | review | R2 | 108 | 216 | 8,284,310 | 325,265 | 47,200 | 8,656,991 | 740 | 0 | 0 | 0 | 740 |
| C2 | baseline | adjudication | R2 | 32 | 64 | 1,202,927 | 178,546 | 20,495 | 1,402,032 | 296 | 0 | 0 | 0 | 296 |
| C2 | blind | adjudication | U | 47 | 94 | 2,743,243 | 258,644 | 28,137 | 3,030,118 | 376 | 0 | 222 | 0 | 154 |
| C2 | candidate | review | R1 | 93 | 186 | 6,266,032 | 223,245 | 36,638 | 6,526,101 | 552 | 0 | 0 | 0 | 552 |
| C2 | candidate | adjudication | R1 | 49 | 98 | 2,449,483 | 241,753 | 19,965 | 2,711,299 | 265 | 0 | 0 | 0 | 265 |
| C3 | baseline | review | R1 | 88 | 176 | 6,143,240 | 217,050 | 32,727 | 6,393,193 | 510 | 0 | 0 | 0 | 510 |
| C3 | baseline | adjudication | R1 | 47 | 94 | 2,386,566 | 214,993 | 23,413 | 2,625,066 | 321 | 0 | 67 | 0 | 255 |
| C3 | baseline | repair | R1 | 142 | 150 | 6,723,573 | 197,865 | 35,920 | 6,957,508 | 2913 | 2233 | 0 | 0 | 680 |
| C3 | candidate | review | R1 | 66 | 132 | 3,213,167 | 150,719 | 29,561 | 3,393,579 | 471 | 67 | 0 | 0 | 404 |
| C3 | candidate | adjudication | R1 | 46 | 92 | 1,755,968 | 142,250 | 20,530 | 1,918,840 | 276 | 0 | 0 | 0 | 276 |
| C3 | candidate | repair | R1 | 129 | 135 | 6,496,604 | 188,659 | 41,045 | 6,726,443 | 2160 | 1196 | 79 | 179 | 706 |
| C3 | candidate | re-review | R2 | 51 | 102 | 2,394,449 | 340,384 | 29,188 | 2,764,123 | 753 | 0 | 64 | 323 | 366 |
| C4 | baseline | review | R1 | 79 | 158 | 5,682,104 | 217,534 | 43,701 | 5,943,497 | 614 | 0 | 168 | 0 | 445 |
| C4 | baseline | adjudication | R1 | 55 | 110 | 3,601,939 | 299,578 | 31,045 | 3,932,672 | 412 | 0 | 170 | 0 | 242 |
| C4 | baseline | repair | R1 | 175 | 181 | 16,823,539 | 547,903 | 63,058 | 17,434,681 | 2537 | 410 | 1168 | 0 | 959 |
| C4 | baseline | review | R2 | 78 | 156 | 6,120,567 | 364,154 | 43,673 | 6,528,550 | 1277 | 0 | 141 | 601 | 536 |
| C4 | blind | adjudication | U | 52 | 104 | 4,171,459 | 341,220 | 35,219 | 4,548,002 | 436 | 0 | 235 | 0 | 202 |
| C4 | candidate | review | R1 | 60 | 120 | 3,757,842 | 176,828 | 29,345 | 3,964,135 | 447 | 0 | 0 | 0 | 447 |
| C4 | candidate | adjudication | R1 | 30 | 60 | 1,401,522 | 166,056 | 19,085 | 1,586,723 | 271 | 0 | 0 | 0 | 271 |
| C4 | candidate | repair | R1 | 189 | 193 | 15,483,823 | 427,907 | 59,422 | 15,971,345 | 2747 | 1537 | 94 | 0 | 1116 |
| C4 | candidate | re-review | R2 | 81 | 162 | 6,008,785 | 241,164 | 40,723 | 6,290,834 | 659 | 0 | 143 | 0 | 516 |
| C5 | baseline | review | R1 | 51 | 102 | 2,711,062 | 188,098 | 25,316 | 2,924,578 | 395 | 0 | 0 | 0 | 395 |
| C5 | baseline | adjudication | R1 | 28 | 56 | 1,128,262 | 166,413 | 20,785 | 1,315,516 | 285 | 0 | 174 | 0 | 111 |
| C5 | baseline | repair | R1 | 56 | 60 | 2,297,630 | 156,999 | 24,533 | 2,479,222 | 2069 | 1632 | 150 | 0 | 286 |
| C5 | baseline | review | R2 | 57 | 114 | 3,386,322 | 189,348 | 36,239 | 3,612,023 | 552 | 0 | 0 | 0 | 552 |
| C5 | baseline | adjudication | R2 | 20 | 40 | 728,651 | 145,370 | 20,561 | 894,622 | 282 | 0 | 224 | 0 | 58 |
| C5 | blind | adjudication | U | 33 | 66 | 1,618,178 | 244,946 | 27,553 | 1,890,743 | 402 | 0 | 243 | 0 | 159 |
| C5 | candidate | review | R1 | 37 | 74 | 1,828,550 | 179,601 | 23,647 | 2,031,872 | 385 | 0 | 0 | 0 | 385 |
| C5 | candidate | adjudication | R1 | 31 | 62 | 1,244,695 | 214,044 | 25,678 | 1,484,479 | 361 | 0 | 100 | 0 | 260 |
| C5 | candidate | repair | R1 | 26 | 32 | 646,054 | 116,362 | 10,476 | 772,924 | 1609 | 1406 | 64 | 0 | 139 |
| C5 | candidate | re-review | R2 | 20 | 40 | 646,437 | 100,771 | 13,727 | 760,975 | 186 | 0 | 0 | 0 | 186 |
| C6 | baseline | review | R1 | 108 | 216 | 9,893,839 | 314,841 | 56,135 | 10,265,031 | 1071 | 78 | 0 | 0 | 993 |
| C6 | baseline | adjudication | R1 | 45 | 90 | 2,115,918 | 426,636 | 26,465 | 2,569,109 | 1285 | 0 | 992 | 0 | 293 |
| C6 | baseline | repair | R1 | 123 | 129 | 6,932,275 | 190,214 | 43,558 | 7,166,176 | 906 | 82 | 62 | 0 | 762 |
| C6 | baseline | review | R2 | 101 | 202 | 10,101,971 | 295,840 | 57,276 | 10,455,289 | 1057 | 0 | 137 | 81 | 839 |
| C6 | candidate | review | R1 | 89 | 178 | 6,868,619 | 255,164 | 41,277 | 7,165,238 | 650 | 0 | 0 | 0 | 650 |
| C6 | candidate | adjudication | R1 | 51 | 102 | 2,755,631 | 236,207 | 24,960 | 3,016,900 | 361 | 0 | 0 | 0 | 361 |
| C6 | candidate | repair | R1 | 131 | 137 | 5,881,674 | 255,871 | 34,615 | 6,172,297 | 1911 | 1279 | 0 | 0 | 632 |
| C6 | candidate | re-review | R2 | 85 | 170 | 5,760,637 | 206,968 | 37,561 | 6,005,336 | 671 | 0 | 0 | 0 | 671 |
| C6 | candidate | repair | R2 | 13 | 19 | 172,614 | 36,264 | 2,594 | 211,491 | 67 | 0 | 0 | 0 | 67 |
| C6 | candidate | re-review | R3 | 58 | 116 | 3,302,083 | 195,316 | 37,423 | 3,534,938 | 551 | 0 | 0 | 0 | 551 |

Run total: 59 measured agent calls and 247,615,104 provider-reported tokens over
12.33 h elapsed, decomposing into 6.67 h active work,
2.57 h model or queue stall, 2.76 h waiting on human
permission grants, and 0.33 h long-running tool execution.

## Per-case results

Tokens are the sum over that arm's review, adjudication, repair and re-review calls — the quantity
the kill condition names. Arm end-states differ because each arm ran its own policy's cycle to that
policy's own stopping point.

| Case | Stratum | Arm | Calls | Total tokens | Policy elapsed s | Active s | Token saving | Active saving | End state |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | non-high | baseline | 9 | 26,304,972 | 5318 | 2796 | — | — | stopped at the round-4 cap, not converged: 2 Blockers open |
| C1 | non-high | candidate | 6 | 15,348,807 | 2908 | 1862 | 41.65% | 33.42% | converged at pass 3; no Blocker; residuals recorded |
| C2 | non-high | baseline | 5 | 21,985,857 | 3100 | 2107 | — | — | converged at pass 2; one Low deferred |
| C2 | non-high | candidate | 2 | 9,237,400 | 817 | 817 | 57.98% | 61.23% | converged at pass 1; nothing blocking, no repair needed |
| C3 | non-high | baseline | 3 | 15,975,767 | 1511 | 1444 | — | — | stopped after pass 2, sustained findings open |
| C3 | non-high | candidate | 4 | 14,802,985 | 2397 | 1752 | 7.34% | -21.28% | stopped after pass 2, 2 repair-induced Blockers open |
| C4 | non-high | baseline | 4 | 33,839,400 | 4430 | 2182 | — | — | stopped after pass 2, 5 Blockers open |
| C4 | non-high | candidate | 4 | 27,813,037 | 2586 | 2349 | 17.81% | -7.66% | stopped after pass 2, 2 findings still open |
| C5 | high-risk | baseline | 5 | 11,225,961 | 1951 | 1403 | — | — | stopped after pass 2; 10 of 11 sustained, 6 repair-induced |
| C5 | high-risk | candidate | 4 | 5,050,250 | 1134 | 970 | 55.01% | 30.85% | converged at pass 2; all 3 sustained findings closed |
| C6 | high-risk | baseline | 4 | 30,455,605 | 4160 | 2886 | — | — | stopped after pass 2, 16 findings open |
| C6 | high-risk | candidate | 6 | 26,106,200 | 2932 | 2932 | 14.28% | -1.59% | converged at pass 3; all projections byte-identical |

## Medians

The kill condition computes medians over the four non-high-risk cases only.

| Measure | C1 | C2 | C3 | C4 | Median | Threshold | Meets threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Total review + adjudication + repair model tokens | 41.65% | 57.98% | 7.34% | 17.81% | **29.73%** | ≥ 30% | **No, by 0.27 pp** |
| Active time (proxy; the predeclared wall-clock measure is undecidable on this host) | 33.42% | 61.23% | -21.28% | -7.66% | **12.88%** | ≥ 30% | **No** |

With four observations the median is the mean of the middle two, so it is 17.81% and 41.65%
averaged. **The token clause fails by 0.27 percentage points.** That margin is thinner than the
method bounds disclosed under Limitations, which push in both directions: capping the baseline at four
rounds understates baseline cost and so understates the saving, while omitting one candidate
adjudication call understates candidate cost and so overstates it. The token clause should therefore
not be treated as an independent basis for the verdict — the protected-class clause is, and it is not
marginal.

The two cases that hold the median down are C3 and C4, and the reason is visible in the raw table
rather than inferred: on both, the repair call dominates the arm's cost and both arms paid it. C4's
baseline repair was 17,434,681 tokens against the candidate's 15,971,345; C3's were 6,957,508 against
6,726,443. The candidate policy narrows reviewing, not repairing, so where a case's cost is
repair-dominated there is little left for it to save.

## High-risk cases, reported separately

Never averaged into the medians above.

| Case | Token saving | Active saving | Candidate protected-class misses |
| --- | --- | --- | --- |
| C5 | 55.01% | 30.85% | 0 |
| C6 | 14.28% | -1.59% | 1 — High, public contract |

## Missed-finding analysis

### Why the per-arm adjudications could not answer this

Each arm adjudicated its own findings as it ran, and those verdicts disagree with each other on
substantively identical defects. On C3 the baseline arm sustained the `map_mismatch` timeout
misreport as a Blocker while the candidate arm refuted the same defect on authority. On C4 the
mirror happened: the candidate sustained the deleted-detection-guidance finding that the baseline
arm refuted. A miss count taken from those verdicts would measure adjudicator variance, not review
coverage. Nothing in the missed-finding analysis below comes from them.

### How the union was adjudicated

Both arms' first review pass is the only stage where they saw byte-identical input, so that stage is
what the comparison uses; later rounds are reported above as cost and convergence evidence.

The 120 first-pass findings were assembled into six per-case union files with policy identity
removed: identifiers renumbered `<case>-U-nn`, ordering made policy-independent by hashing the
original identifier, and every reference to a policy name, pass number or sibling finding id
scrubbed. A mechanical check confirmed zero residual identity leaks. Six fresh `finding-adjudicator`
agents — one per case, each on its own pristine worktree at the frozen revision, none of which had
run either arm — each adjudicated its case's union, ruled severity and protected class on its own
judgement rather than deferring to what a finding asserted, and grouped the findings into **defect
clusters**, where one cluster is one underlying defect.

The cluster grouping is what makes the comparison meaningful. Two findings in the same cluster
describe the same defect in different words, so an arm has only genuinely *missed* something when a
sustained cluster contains findings from the other arm alone. The private key mapping blinded
identifiers back to arms was not available to any adjudicator and was applied only afterwards.

### Result

| Case | Stratum | Sustained clusters | Reached by both arms | Candidate missed | of those, protected-class | of those, Blocker/High |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | non-high | 9 | 4 | 3 | 0 | 0 |
| C2 | non-high | 7 | 5 | 1 | 0 | 0 |
| C3 | non-high | 7 | 4 | 3 | 1 | 0 |
| C4 | non-high | 15 | 9 | 5 | 1 | 1 |
| C5 | high-risk | 7 | 5 | 2 | 0 | 0 |
| C6 | high-risk | 8 | 4 | 2 | 1 | 1 |

The baseline arm also missed sustained clusters — 1 on C2, 1 on C4, 2 on C1 (one of them High), 2 on
C6, 0 on C5 — which the kill condition does not score, because it is one-directional by design. It
is recorded because it bears on the intent's second assumption.

### The three protected-class findings the candidate missed

Each was sustained by the independent adjudicator, assigned its protected class by that adjudicator,
and traced to the baseline arm alone through the private key.

**1. C4 — High, security class.** Blinded `C4-U-17`, originating finding `C4-B-R1-07`, baseline arm,
its cluster containing no candidate finding. Item 6 of `adversarial-reviewer.md:235` was replaced
with routing plus an explicit "Do not emit a threat finding", while `SKILL.md:538` dispatches
`security-reviewer` only when the diff trips an enumerated boundary list that expressly excludes
"ordinary prompt wording with none of those effects". The adjudicator additionally found that
`security-reviewer.md:86-88` still asserts the contrary premise — "For diffs that don't touch any of
the above, the adversarial-reviewer's implementation-stage 'Security and privacy' check is
sufficient" — which the change invalidated without updating. Consequence: a sub-threshold diff
carrying a real threat receives zero threat coverage, and the one reviewer that can see it is
instructed to stay silent.

Worth stating plainly, because it cuts against the arm that found it: **the baseline arm's own
adjudicator refuted this finding**, reasoning that item 6 retained a detection obligation and that
the change added a referral escape. The independent adjudicator overturned that. So the clause fires
on a defect the baseline arm found and then discarded — which is the blind pass doing exactly the
job it was specified for.

**2. C6 — High, public-contract class, on a high-risk case.** Blinded `C6-U-16`, originating finding
`C6-B-R1-07`, baseline arm. `pack.toml` and `plugin.json` both read `2.21.0`, which
`docs/product/changelog.md:57` records as the released, dated `## [core][2.21.0] — 2026-09-01`
whose Highlights already claim the behaviour this change implements — a release cut eleven commits
earlier on the same branch, which the adjudicator confirmed is legitimate evidence rather than a
frozen-checkout artefact. It ruled directly that a version not moving for a published-behaviour
change is a public-contract consequence, because the pack version is the adopter-facing identifier
of what the pack does. AC31 is literally satisfied by `2.21.0` and therefore cannot catch it.

**3. C3 — Medium, public-contract class.** Blinded `C3-U-08`, originating finding `C3-B-R1-07`,
baseline arm. `deadline_exceeded` becomes the fifteenth entry of `REQUIRED_DIAGNOSTIC_CODES` while
`render_diagnostic` still emits `"version": "knowledge-diagnostic.v1"`, against the spec's
"Ask first — Change a versioned contract … vocabulary" boundary. The adjudicator resolved the
apparent tension with AC37's non-exhaustive "Codes include" against the change: the two other
unlisted codes are each authorized by an accepted criterion, whereas AC19 names no code for a
deadline, so this extension has no accepted backing.

### What the candidate did not miss

The candidate matched the baseline on every other protected-class cluster in the corpus, including
the ones that mattered most: C5's data-loss and mixed-version projection-drift Blocker (both arms),
C3's destructive-operation and data-loss cluster where a swallowed deadline reaches
`shutil.rmtree(topics)` (both arms), C6's public-contract cooled-resolution regression and its
projection-drift Blocker (both arms), and C1's human-approval Blocker for editing an
approval-pinned spec row — which the candidate found in its **first** pass and the baseline reached
only in its **third**.

### Repair-induced findings

Counted across all rounds, 28 sustained findings were attributed by the adjudicating agent to an
earlier repair rather than to the original change: **24 in baseline arms against 4 in candidate
arms**, and 4 repair-induced Blockers in baseline arms against 1 in candidate arms. The mechanism is
visible case by case. C5's baseline repair of a *Concern* introduced a *Blocker* — an AC20
arrival-spread guard that cannot fail for the condition it names, reinstating a mechanism a sibling
harness had already abandoned as non-probative at 40× the threshold. C3's baseline repair introduced
fresh projection drift by adding docstrings to the pack source and not its projections. C6's
baseline repair reversed the decision the original commit recorded as measured, left `make
lint-ruff` red on its own line, and published two Highlights bullets the reviewer disproved by
running the released scripts against the repaired ones.

The candidate arm is not exempt: its C1 repair wrote a relative link that resolved one directory too
deep, its C6 repair left two projections byte-stale on statement ordering, and its C3 repair left
the `/now/` projection stale and published a false retry claim. In every one of those three cases
the **focused** re-review caught the repair's own defect, which is direct evidence for the intent's
second assumption even though the first assumption failed.

## Economic findings and routing

The verdict answers whether the combined candidate should ship. It does not answer which parts of
the delivery loop are necessary, duplicated, misplaced, or separately improvable. The retained
corpus supports the following narrower conclusions:

| Finding | Evidence | Interpretation | Disposition |
| --- | --- | --- | --- |
| The combined candidate is unsafe | Three baseline-only protected clusters: C3 public-contract, C4 security, C6 public-contract | The candidate cannot replace the current policy as tested | Keep the kill; do not weaken the protected-class guardrail |
| Initial broad review is not redundant | Of 53 sustained blind-union clusters, 31 appeared in both arms, 16 were candidate misses, and 6 were baseline misses; the candidate misses include all three protected misses | One broad pass still contributes independent material coverage, and a one-shot reviewer result is stochastic | Retain an initial broad review; do not infer completeness from one arm or one Clean result |
| Later whole-change re-review is partly avoidable | Baseline broad reviews and candidate broad-plus-focused re-reviews used the same 13 reviewer calls, but review tokens fell from 84.7M to 54.3M (35.8%) when repair checks were focused | The measured saving came from narrowing context, not merely reducing call count; later broad rounds also generated repeated repair work | Test focused re-review separately, without consequence-bound blocking |
| Adjudication is costly but not shown redundant | Adjudication used 17.3M baseline tokens and 12.3M candidate tokens; per-arm adjudicators disagreed on substantively similar findings | Adjudication protects against reviewer error, but its predicates and defect clustering need to be clearer and cheaper | Retain adjudication for findings; investigate deduplicated clusters and evidence-complete finding records before reducing it |
| Faulty repair is a separate cost centre | Repair used 37.8M baseline tokens and 31.8M candidate tokens; 28 sustained findings were repair-induced, 24 baseline and 4 candidate | Review scheduling alone cannot remove repair cost, especially in C3 and C4 | Create a separate repair-correctness hypothesis: better repair inputs, smaller repair scope, and targeted verification |
| Convention discovery happens too late | 22 of 67 sustained findings were repository obligations, split 11/11 between arms | These checks are necessary today but economically misplaced in late semantic review | Shift touched-path obligations into the implementer brief and deterministic pre-review checks |
| This experiment is itself expensive | 59 measured calls used 247.6M provider-reported tokens and 12.33 hours elapsed | A full six-case replay is suitable for a consequential policy decision, not every small tuning change | Use isolated ablations and cheaper leading indicators before another full validation |

The review answer is therefore mixed. The first broad review and triggered specialist coverage are
not shown to be unnecessary. Adjudication is also doing real work because reviewers and
adjudicators disagree. The economically weak part is repeatedly resampling the entire change after
a bounded repair: the corpus supports replacing that step with focused re-review as a new, isolated
hypothesis, while preserving the initial broad pass and protected-class coverage.

### Where the token cost went

| Phase | Baseline calls | Baseline tokens | Candidate calls | Candidate tokens | Saving |
| --- | ---: | ---: | ---: | ---: | ---: |
| Review | 13 | 84,672,955 | 13 | 54,331,805 | 35.8% |
| Adjudication | 9 | 17,334,811 | 6 | 12,263,834 | 29.3% |
| Repair | 8 | 37,779,796 | 7 | 31,763,040 | 15.9% |
| **Total** | **30** | **139,787,562** | **26** | **98,358,679** | **29.6%** |

The candidate's review row contains six broad-review calls and seven focused re-review calls; the
baseline row contains thirteen broad-review calls. The review call count therefore did not fall.
The 35.8% saving came from giving later reviewers a smaller subject and purpose. Repair moved much
less, which explains why the overall economics missed the bar despite a large review-phase saving.

### What happened to the findings

The corpus has three different denominators: 148 raw findings emitted across all rounds, 67 formally
sustained arm-local findings plus one directly verified candidate defect, and 53 sustained defect
clusters after the blind union grouped the same defect reported in different words. The first
measures review volume, the second repair demand, and the third comparative coverage; they should
not be substituted for one another.

| Outcome | Baseline | Candidate | What it means |
| --- | ---: | ---: | --- |
| Raw findings emitted | 90 | 58 | The candidate generated less review churn, but the arm stopping conditions differ |
| Sustained or directly verified | 34 | 34 | Lower raw volume did not reduce the count of accepted defects within the arm records |
| Repair-induced sustained findings | 24 | 4 | Most of the baseline's accepted churn followed its own repairs |
| Pending or capped without adjudication | 24 | 0 | The baseline count is incomplete because capped C1 still had open work |

These arm-local dispositions cannot measure coverage because their adjudicators disagreed. The
blind union is the coverage view: 53 sustained defect clusters, with 31 reached by both arms, 16 by
the baseline only, and 6 by the candidate only. That is why less churn is promising but cannot be
treated as proof that the omitted review work was unnecessary.

Repair quality is actionable rather than merely an experimental nuisance. A repair brief can carry
the accepted finding, the closure predicate, affected files and contract bytes, and touched-path
repository obligations; the implementer can then run the smallest verifier that proves that repair
before returning it. Focused re-review remains necessary because it caught all three candidate
repair defects observed in C1, C3, and C6, but it becomes a backstop for a better repair process
rather than the first place predictable convention failures are discovered.

<!-- filled in after the independent blind adjudication -->

## A cost driver neither policy addresses

The owner observed during the run that part of this cost is structural to a monorepo: interdependence
between subsystems grows over time, and reviewers and implementers do not arrive knowing each
repository's ground rules. The finding corpus supports that, and it bears directly on whether review
scheduling is the right lever.

Of the 67 sustained findings, 22 — one third — are unmet repository-convention obligations rather
than defects in the logic the change was written to alter. Grouped by the rule they breach:

| Convention class | Sustained findings | Baseline | Candidate | Cases affected |
| --- | --- | --- | --- | --- |
| Projection drift: `.apm/` edited without regenerating `.claude/`, `.agents/`, `.codex/`, `packages/agentbundle/_data/` | 8 | 4 | 4 | C2, C3, C4, C5, C6 |
| Register or backlog record left contradicting the tree | 7 | 3 | 4 | C1, C3, C5 |
| Version bump and changelog entry not paired | 3 | 1 | 2 | C3, C4 |
| Sealed-plan or frozen-spec deviation unrecorded | 2 | 1 | 1 | C1, C5 |
| Eval-harness obligation keyed to the same "non-cosmetic" predicate | 1 | 1 | 0 | C1 |
| Control that cannot fail / no verification artifact | 1 | 1 | 0 | C5 |

The keyword grouping runs over each finding's recorded consequence summary rather than its full text,
so 22 is a floor rather than an estimate.

Two things follow. First, projection drift is the most repeated defect in the corpus — five of six
cases — and **both** policies found it in all five. Second, and more consequential for this child
intent: the convention classes are distributed almost evenly across the two arms, 11 baseline and
11 candidate. This cost is symmetric. A policy that changes how much reviewing happens cannot reduce
it, because the reviewing is not what produces it — the implementer not knowing the rule is, and
both arms then pay the same repair cost. The C4 baseline repair shows the compounding form: it could
not remove a contradictory instruction because a test pins that exact phrase, so it appended
exception clauses instead, and the same happened to the "exclusively" qualifier.

The strongest form of the evidence is that the repairs themselves breached the same rules. C3's
baseline repair added three docstrings to the pack source and not to its projections, so the four
files that were byte-identical before the change became two distinct blobs — projection drift
introduced by the repair dispatched to fix projection drift. C6's candidate repair left two of five
projections byte-stale on statement ordering. C1's candidate repair wrote a relative link that
resolved one directory too deep. In each case a reviewer then had to find it, and a further repair
had to fix it.

The lever this points at is upstream of review scheduling, and the architecture already provides the
seam for it: the `implementer` subagent is a separate role precisely so that the applicable ground
rules can be inlined into its brief. That makes the remedy a brief-content change at an existing
boundary rather than a new mechanism — the orchestrator already inlines depth this way for
`security-reviewer` (the `security-checklists` modules) and for `quality-engineer` (the
`operational-safety` modules), because a subagent has no `Skill` tool and cannot self-discover them.
The same inlining applied to the implementer, carrying the projection, release-surface, and register
obligations that the change's touched paths trigger, would remove the class at its source instead of
paying a reviewer to rediscover it once per change and a repair round to fix it.

That work is a sibling to this intent under the parent, not a reshape of it. Post-adjudication
obligation delivery now has an explicit home in [work-loop repair
correctness](../intents/work-loop-repair-correctness.md) (`Impact 2`); upstream spec and plan quality
remain with progressive authoring (`Impact 6`) and the existing `agent-authoring-input-quality`
brief. It is recorded here as measured evidence because this child's boundary is reviewer scope and
stopping semantics.

## Limitations

Each limitation below states which direction it pushes the result, so a reader can see whether it
could have manufactured the verdict.

**Elapsed time is not a controlled variable on this host.** The run shared a machine with four other
concurrent Claude Code sessions in sibling worktrees, at load averages between 10 and 113. Across
all measured calls, elapsed time decomposes into 54% active work, 21% model or queue stall, 22%
human permission waits, and 3% tool execution. One C2 repair call recorded 1,155,768 ms elapsed
against 162,833 ms active.
Because stall arrives in bursts that hit whichever arm is running at the time, the predeclared
median wall-clock comparison cannot be read off elapsed time. The tables report elapsed,
policy-attributable elapsed (elapsed minus human permission waits), and active time separately, and
the survive/kill calculation treats the wall-clock clause as undecided on this host rather than
substituting a different measure. Direction: neutral — the contamination is not systematically
aligned with either arm.

**Permission waits were separated from tool execution by inspecting the pending request.** A gap
longer than 60 seconds between a tool request and its result is a permission prompt or a slow
command, and the two are indistinguishable from timing alone. The classifier resolves them by
reading the pending tool call and treating a `Bash` invocation of a test, build, or hashing command
as execution rather than a prompt. On this run that reclassification moved nothing: measured tool
execution above the 60-second threshold was exactly 0 ms, because the only test run inside a repair
call completed in 3.64 s. Direction: neutral.

**Both arms were sequenced for arm order but run concurrently across cases.** The pre-registration
alternated which arm ran first per case, and that was honoured. Once the wall-clock clause was
already compromised, cases were run concurrently to make the run finishable, which raised the load
the run imposed on itself. Direction: inflates elapsed time for both arms; no effect on tokens or
on findings.

**The frozen corpus is reviewed against a `origin/main` that has moved.** Each worktree is a
historical revision inside a repository whose `origin/main` has advanced well past it, so a reviewer
that consults `origin/main` can produce a finding that was not true when the change was authored.
C1 baseline round 2 produced exactly one such finding, a pack version that looks like a regression
only against the newer released version. Every adjudication from that point on was given the frozen
checkout as explicit context and instructed to refute that class, and the adjudicators confirmed
case by case which findings did and did not depend on it. C1 baseline round 1's adjudication
predates that instruction; no finding in it rested on `origin/main`. Direction: adds noise to the
baseline arm on C1 only, which slightly inflates baseline cost.

**Repairs did not run the repository's gate suite, and projections were synced by hand.** Repair
agents were forbidden from running `make build-self`, self-host writes, and the full gate chain,
because the worktrees are measurement fixtures on a machine with active peer sessions. Where a
sustained finding required regenerated projections, the implementer applied the equivalent edit by
hand and recorded that it had done so. The consequence is that projection-drift repairs demonstrate
byte-identity of a hand-synced tree rather than that the projection mechanism reproduces it, which
the C5 focused re-review recorded explicitly as a residual. Direction: understates repair cost in
both arms roughly equally, since both arms hit projection findings.

**One candidate finding was adjudicated by the orchestrator rather than by a dispatched
adjudicator.** `C1-C-R2-01`, a dangling relative markdown link, was confirmed directly by listing
the target directory, and its repair was dispatched without a `finding-adjudicator` call. Direction:
understates the candidate arm's cost by one adjudication call on C1.

**The baseline arm was capped at four review rounds.** The baseline policy iterates until a round
sustains nothing above a deferred Nit. On C1 it did not converge: sustained counts by round ran
3, 3, 7, and the arm was stopped after round 4 with open findings recorded rather than iterated
further. Direction: understates baseline cost, so it cannot manufacture a candidate win.

**Per-arm adjudications disagreed with each other on substantively identical findings.** The clearest
case is C3, where the baseline arm sustained the `map_mismatch` timeout misreport as a Blocker while
the candidate arm refuted the same defect on authority; C4 shows the mirror, where the candidate
sustained the deleted-detection-guidance finding that the baseline arm refuted. This is adjudicator
variance, not a difference between the review policies, and it is the reason the missed-finding
analysis below rests on the single blind adjudication of the union rather than on the per-arm
verdicts. Direction: would corrupt any miss count taken from per-arm adjudications, which is why
none is taken from them.

**Six cases is the predeclared corpus, not a statistically powered sample.** The kill condition asks
for medians across the four non-high-risk cases, so a median rests on four observations and a single
case moves it. This is the corpus the owner predeclared and it was not enlarged or reduced after
seeing results.

## Survive/kill calculation

### Verdict: Killed

Two of the three predeclared clauses fire. They are not equally strong, and the difference matters
for anyone deciding what to do next: the protected-class clause fires decisively, while the cost
clause fires by 0.27 percentage points and should not be leaned on.

The kill condition, quoted from the child intent exactly as predeclared on 2026-09-09 before any
case ran:

> Kill or reshape this candidate if a paired six-change spike misses any independently adjudicated
> sustained finding with a security, privacy, data-loss, migration, mixed-version, public-contract,
> destructive-operation, or human-approval consequence that the baseline found; misses more than one
> other sustained material blocker or high-severity finding; or fails to reduce both median
> review-stage wall-clock time and median total review, adjudication, and repair model tokens by at
> least 30% across the four non-high-risk cases.

**Clause 1 — missed protected-class findings. FIRES.** The clause requires *any* such miss. There
are three: C4 High/security, C6 High/public-contract on a high-risk case, and C3
Medium/public-contract. Each was sustained by an independent adjudicator blind to arm identity, each
was assigned its protected class by that adjudicator, and each traces to the baseline arm alone
through a cluster containing no candidate finding.

**Clause 2 — more than one *other* sustained Blocker or High. DOES NOT FIRE.** The candidate's two
Blocker/High misses are the C4 and C6 findings already counted under clause 1, so the count of
*other* such misses is 0, which is not more than one.

**Clause 3 — the cost thresholds. FIRES, but marginally, and it is not load-bearing.** The clause
requires reducing *both* medians by at least 30%. The median token saving across the four
non-high-risk cases is **29.73%** (C1 41.65%, C2 57.98%, C3 7.34%, C4 17.81%), which fails the 30%
bar by **0.27 percentage points**. The wall-clock half cannot be satisfied either way: the
predeclared measure is not defensibly measurable on this host, and the closest honest proxy, active
time, has a median saving of 12.88%.

That 0.27 pp margin is smaller than the method bounds recorded under Limitations, and those bounds
push in both directions — capping the baseline at four rounds understates baseline cost and so
understates the saving, while omitting one candidate adjudication call understates candidate cost
and so overstates it. A reader should treat the token half as "did not clear the bar, within noise of
it", not as a decisive result. **The verdict does not depend on this clause.** Clause 1 does, and
clause 1 is not marginal: three protected-class misses where the condition requires zero.

One correction worth recording, because an earlier draft of this document reported the median as
24.5%. That figure came from measuring C4's baseline round-2 review while the call was still in
flight, at 2,723,742 tokens; its completed cost is 6,528,550. Re-measuring every call from its
finished transcript moved C4's token saving from 7.4% to 17.81% and the median from 24.5% to 29.73%.
The corrected figures are the ones in the tables above.

### Evidence retention

Owner decision, 2026-09-10: retain this findings report only. Raw arm reports, blinded unions,
measurement rows, finding rows, blinding keys and helper scripts were deliberately not retained in
the repository. The tables preserve the reported aggregates and method, but they cannot be
recomputed from repository artifacts alone.

### What this kills, and what it does not

The killed proposition is the specific bet: that consequence-bound blocking plus focused re-review
would cut both cost measures by 30% while retaining material coverage. It did neither.

Three findings survive the kill and belong to the parent, because they were measured rather than
assumed:

- **The intent's second assumption held.** A focused reviewer given the sustained finding, its fix,
  the affected contract and dependency context did verify closure reliably, and caught three
  repair-induced defects that a broad resample would have had to find as well — including one it
  proved with a failing roster test and one it proved by hashing rather than trusting a report.
- **The intent's first assumption held in the direction it predicted, but not enough to pay.** The
  baseline's later broad rounds did mostly resample its own repairs: 24 of its sustained findings
  were repair-induced against the candidate's 4, and C1's baseline diverged across four rounds
  (3, 3, 7 sustained) without converging. The candidate reached C1's human-approval Blocker in one
  pass where the baseline needed three. That saving was real but concentrated in review calls, while
  cost on C3 and C4 is repair-dominated, which the candidate does not touch.
- **A third of sustained findings are unmet repository conventions, evenly split across both arms**,
  and that cost is invisible to any change in review scheduling. The section above records the
  evidence and names the implementer brief as the existing seam for it.

### Owner decisions left pending

The spike does not simulate owner authority, so the following remain open and are recorded rather
than resolved:

1. **Resolved 2026-09-09 — reshape the child.** The owner selected a replacement sibling,
   [work-loop focused re-review](../intents/work-loop-focused-re-review.md), that keeps the initial
   broad review and existing blocking semantics, tests focused post-repair review on identical
   repaired bytes, and omits consequence-bound blocking and revision-bound reuse. The replacement
   carries its own predeclared kill condition.
2. **Residual-risk acceptance on the experimental arms.** No arm's residuals were accepted; every
   repair lived only in a disposable worktree and none is proposed for merge. C1's candidate arm
   surfaced but did not take the one route that needed owner re-approval — amending an
   approval-pinned spec after a recorded withdrawal directive — and left it explicitly pending.
3. **Whether the wall-clock clause should be re-run on a quiet host.** The token clause fails on its
   own, so re-running would not change the verdict. It would only settle whether the wall-clock
   half also fails, which matters if the child is reshaped rather than dropped.
