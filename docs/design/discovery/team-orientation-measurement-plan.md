---
type: measurement-plan
slug: team-orientation-measurement-plan
status: proposed
surface: cross-platform
evidence_level: mixed
updated: 2026-09-04
---

# Measurement plan — team orientation redesign

This plan tests whether the redesign helps a champion move a cohort from first
contact to routine use. It does not treat a visit, an install, or a click as
proof of understanding or adoption.

The redesign remains a hypothesis. The only working behavioural instrument is
the GitHub repository traffic API, and it cannot see the published site,
comprehension, intent, or cohort use. Every other answer below is either gathered
manually or remains unavailable.

## What we are trying to learn

1. Can a first-time reader tell what this is, who it is for, and why they should
   care after five seconds?
2. Can a reader explain the operating model in their own words, including the
   work lifecycle and the team-adoption lifecycle?
3. Do readers understand where people decide, what the system refuses to do on
   its own, and how Jira or Linear relates to the system?
4. Does one canvas work for the champion, engineer, platform lead, and budget
   holder, or does one role leave without the part it needs?
5. Do the checkable proofs help a skeptical reader distinguish a real safeguard
   from an unsupported claim?
6. Does the artifact survive transfer from a champion to another person without
   a live explanation?
7. Can a platform lead complete the adopt path from the documentation guides
   index without help from the champion?
8. Do readers find a guided route instead of bypassing both surfaces for raw
   source, and can they resolve a documentation search?
9. Does initial success spread to the intended cohort rather than stopping with
   one installer?
10. Does use persist after the first success, including under normal work after
    the rollout period?

## Measures

Each measure answers one question above. `Observed` means a real instrument
exists today. `Manual` means a person must gather and assemble the evidence.
`Unavailable` means no instrument exists and this plan proposes none.

### M1. Five-second scan completeness — question 1

- **Status:** `manual`
- **What it measures:** Whether a first-time reader can answer all three
  orientation questions from the visible marketing-home content alone: what is
  this, who is it for, and should I care?
- **Collection:** Show the above-fold surface for five seconds, remove it, and
  ask the three questions without prompts. Record each answer and whether all
  three are supported by visible content.
- **Collector:** A neutral facilitator or the redesign owner using a fixed
  script.
- **Cadence:** Once before launch on the current surface, once on the release
  candidate, then after each material above-fold revision.
- **Instrument:** Five-second-scan script and answer sheet derived from the
  Stage 1 validation hook.
- **Baseline:** The heuristic inspection records **two of three answers as
  absent** and *what is this* as only partially answerable. The all-three
  criterion therefore fails, but this is not a participant baseline. No
  tested-reader baseline exists until the first manual session runs, so this
  measure cannot yet show improvement in reader performance.

### M2. Explain-it-back score — question 2

- **Status:** `manual`
- **What it measures:** Whether a reader can explain the model rather than
  repeat its labels. Report the count of fully correct answers out of five and
  retain `correct`, `partial`, or `absent` for every item.
- **Collection:** Ask the five questions in the comprehension check below from
  memory, keep the answer verbatim, and judge the decision or relationship
  expressed rather than internal gate codes.
- **Collector:** The champion-interview facilitator before launch; a facilitator
  who did not onboard the participant for the next-cohort check.
- **Cadence:** Once against the current surfaces before launch, once with the
  next cohort, and after any change to the canvas's model or vocabulary.
- **Instrument:** Part 4 of the champion interview, reused unchanged for the
  next-cohort check.
- **Baseline:** **No score exists.** The interview guide is ready to run, but no
  completed interview result is recorded. Without that pre-redesign score, a
  later score describes comprehension but cannot show improvement.

### M3. Contract comprehension — question 3

- **Status:** `manual`
- **What it measures:** Understanding of the human-decision boundary, the
  one-way Jira or Linear relationship, and actions the system will not take by
  itself.
- **Collection:** Use items 2, 4, and 5 of the same explain-it-back instrument.
  Report each item separately so a total score cannot hide a failed safety or
  source-of-truth concept.
- **Collector:** The same facilitator as M2.
- **Cadence:** With every M2 administration.
- **Instrument:** Champion interview Part 4, items 2, 4, and 5.
- **Baseline:** **None.** The current materials make these claims, but reader
  comprehension has never been checked. The heuristic baseline also records
  eleven appearances of internal gate codes at the model's visual entry point;
  that is a design observation, not a comprehension score.

### M4. Role-stratified comprehension pattern — question 4

- **Status:** `manual`
- **What it measures:** Whether failures cluster by role when all four audiences
  use the same canvas.
- **Collection:** Record the participant's role with M2 and compare item-level
  results for champions, engineers, platform leads, and budget holders. Do not
  combine the roles into one average that can conceal a missing proof type.
- **Collector:** The M2 facilitator.
- **Cadence:** At the release-candidate check and with the next cohort.
- **Instrument:** The five-question explain-it-back answer sheet with a role
  field.
- **Baseline:** **None.** No role-stratified comprehension study exists. The
  current evidence only establishes a live disagreement: the design assumes one
  canvas can serve four entry points, while practitioner literature says generic
  collateral may fail.

### M5. Evidence recognition — question 5

- **Status:** `manual`
- **What it measures:** Whether a skeptical reader can identify which artifact
  shows that a loop cannot approve its own work, that a mechanical gate is
  binding, and that a person made the merge decision.
- **Collection:** After the reader uses only the marketing home, ask them to
  point to the evidence for each claim and explain what it proves. Record
  `located and interpreted`, `located only`, or `not located`.
- **Collector:** The five-second or comprehension-test facilitator.
- **Cadence:** Once on the release candidate and whenever any of the three proof
  artifacts changes.
- **Instrument:** Three-item evidence-recognition task based on the marketing
  content brief's proof set.
- **Baseline:** The heuristic baseline found **five of five load-bearing claims
  without adjacent evidence**. For the three replacement proofs, the current
  baseline is **0 of 3 available beside the claim**. No reader-performance
  baseline exists.

### M6a. Repository-link referral — question 6

- **Status:** `observed`
- **What it measures:** How many unique repository visitors arrive through a
  named chat referrer. It measures a referral path, not champion intent,
  comprehension, or successful transfer.
- **Collection:** Capture the GitHub traffic API's popular-referrers window and
  retain the window dates and unique count. Never sum daily uniques.
- **Collector:** A repository maintainer with the required repository access.
- **Cadence:** At most once per rolling 14-day window when a comparison is
  needed; capture before the window expires.
- **Instrument:** GitHub repository traffic API, popular referrers endpoint.
- **Baseline:** From 2026-08-21 through 2026-09-03, the Microsoft Teams unfurl
  referrer produced **51 views from 12 unique visitors**. The published site
  referred **6 unique visitors** to the repository in the same window. These
  figures do not prove that the link was shared by a champion.

### M6b. Confirmed transfer account — question 6

- **Status:** `manual`
- **What it measures:** What a champion actually sent, to whom, and whether the
  recipient could carry the explanation onward.
- **Collection:** Ask champion-interview questions 12 through 15 about the most
  recent real transfer. Keep the shared artifact and outcome in the
  participant's own words. Do not prompt with the traffic finding or canvas.
- **Collector:** The champion-interview facilitator.
- **Cadence:** Once before launch and once after the next cohort's buy-in stage.
- **Instrument:** Champion interview Part 3, especially question 13.
- **Baseline:** **None.** The traffic baseline shows a referral mechanism but
  cannot establish the sender's intent or the recipient's understanding.

### M7. Adopt-path task completion — question 7

- **Status:** `manual`
- **What it measures:** Whether a platform lead who has never spoken to the
  champion can start from the guides index and complete the adopt path without
  outside explanation.
- **Collection:** Give the platform lead the index and the task, then record
  completion without facilitator help, stops, missing prerequisites, elapsed
  time, first result, and whether the participant can name the final handoff.
- **Collector:** A facilitator who is not the champion.
- **Cadence:** Once on the current index, once on the release candidate, and
  after changes to the start-here route or adopt path.
- **Instrument:** Platform-lead path-completion walkthrough based on the Stage 4
  validation hook and the guides-index completion definition.
- **Baseline:** **No participant completion baseline exists.** The heuristic
  baseline found that the current hub fails two of its three jobs and only
  partly meets the third. It also found that all **21 guide areas** sit in one
  last sidebar group and **21 of 22** guide areas have no direct marketing
  route. These are structural baselines, not a completion rate.

### M8. Repository route pattern — question 8

- **Status:** `observed`
- **What it measures:** Which github.com repository paths people read and which
  named sources refer them. It can reveal continued preference for raw source,
  but it cannot show use of the published guides index.
- **Collection:** Capture window totals from the GitHub traffic API's views,
  popular-paths, and popular-referrers endpoints. Exclude known operator traffic
  and do not interpret clone counts as evaluators.
- **Collector:** A repository maintainer with the required repository access.
- **Cadence:** For one comparable 14-day window before launch and one after;
  additional captures only when a route change creates a specific question.
- **Instrument:** GitHub repository traffic API.
- **Baseline:** The 2026-08-21 to 2026-09-03 window recorded **725 views and 149
  unique visitors**. The README had **68 unique readers**, one raw skill file
  had **12**, `/tree/main/docs` had **6**, and the published site sent **6
  unique referrals** to the repository. **91 of 149 visitors, or 61 percent,**
  had no referrer. The raw-file and docs-directory counts are not measures of
  the published guides index.

### M9. Published-index discovery and search resolution — question 8

- **Status:** `unavailable`
- **What it measures:** The share of published guide-area arrivals that pass
  through the guides index, plus the share of documentation searches that end
  at a useful guide.
- **Collection:** None.
- **Collector:** None.
- **Cadence:** None.
- **Instrument:** None. GitHub Pages has no analytics API in use here, and the
  deploy has no third-party analytics. This plan does not propose one.
- **Baseline:** **None.** The reported 12 raw-skill readers versus 6 repository
  docs-directory readers cannot be used as this baseline because neither count
  observes published-index visits or searches.

### M10. Time to first value (TTFV) — question 9

- **Status:** `manual`
- **What it measures:** Reuse the adoption journey's TTFV definition and its
  three paths: install to first shipped spec for self-serve, demo start to spec
  shipped for a live demo, and buy-in to the first engineer's shipped spec for
  enterprise rollout.
- **Collection:** Use the recorded pack-install time and first `shipped` entry in
  `workspace.toml`; use champion reports for the demo and rollout dates.
- **Collector:** The champion for demo and rollout records; the installer for a
  self-serve record.
- **Cadence:** Per first-use attempt, per demo, and once per cohort rollout.
- **Instrument:** Adoption worksheet containing the timestamps and the relevant
  `workspace.toml` entry.
- **Baseline:** **None for this redesign or a prior cohort.** The inherited
  targets are under 1 hour self-serve, under 30 minutes for a live demo, and
  under 2 weeks from buy-in to the first engineer shipping. Targets are not
  baselines and cannot show improvement by themselves.

### M11. Activation rate — question 9

- **Status:** `manual`
- **What it measures:** Reuse the adoption journey's definition: the percentage
  of engineers who install and ship at least one spec within seven days.
- **Collection:** For the cohort roster, count installed engineers with at least
  one `shipped` entry in `workspace.toml` within seven days of install.
- **Collector:** The champion or platform lead running the cohort rollout.
- **Cadence:** At day 7 for each cohort.
- **Instrument:** Adoption worksheet, cohort roster, install dates, and
  `workspace.toml` shipped entries.
- **Baseline:** **None.** No prior cohort activation rate is recorded. The
  inherited target is greater than 80 percent; it is an absolute test, not
  evidence of improvement.

### M12. Thirty-day retention — question 10

- **Status:** `manual`
- **What it measures:** Reuse the adoption journey's definition: the percentage
  of engineers who shipped a first spec and are still shipping specs at day 30.
- **Collection:** Count engineers with at least one `shipped` entry in weeks 3
  and 4 who also had one in week 1.
- **Collector:** The champion or platform lead, separately from the adoption
  worksheet owner where practical.
- **Cadence:** Once at day 30 for each cohort.
- **Instrument:** Retention worksheet, cohort roster, and week 1 through week 4
  `workspace.toml` shipped entries.
- **Baseline:** **None.** No prior cohort retention rate is recorded. The
  inherited target is greater than 70 percent; it cannot show improvement
  without a prior-cohort value.

### M13. Session-start habit — question 10

- **Status:** `manual`
- **What it measures:** Reuse the adoption journey's definition: whether
  engineers run `workspace-status` first in more than 70 percent of sessions by
  week 4.
- **Collection:** Use the existing self-report survey method until session
  instrumentation exists. Keep the documented proxy, `workspace.toml` active
  entries moving to shipped within one session, separate because it does not
  observe the first command.
- **Collector:** A cohort coordinator who is not answering on behalf of the
  engineers.
- **Cadence:** Weekly during the first four weeks, with the decision reading at
  week 4.
- **Instrument:** Week-4 session-start survey and the separate
  `workspace.toml` transition proxy.
- **Baseline:** **None.** No prior survey or session instrumentation result is
  recorded. The greater-than-70-percent target is not a baseline.

## Adoption and retention need different instruments

The adoption instrument asks whether the model crosses from a champion to a
cohort. It needs a cohort roster, install dates, buy-in and demo dates, the first
`shipped` entry per engineer, M10 TTFV, and M11 activation at day 7. It ends when
the cohort has had a fair first-use window.

The retention instrument starts from the engineers who reached first value. It
needs week-numbered shipped entries through day 30, the M12 retained-user count,
and the M13 session-start survey. It must preserve the day-7 denominator so
people who never activated are not mislabeled as people who activated and then
reverted.

Do not merge the two worksheets into one funnel score. Peer audit finding F15
shows that factors associated with trying a tool can differ from those associated
with persistence. A short TTFV or high activation rate cannot stand in for
30-day retention, and a retained minority cannot hide a failed rollout.

## Baseline rules

The numerical baselines above come from two sources with different authority:

- The traffic evidence is observed behaviour on github.com during one fixed
  14-day window. It is reproducible only as a new rolling window, not as the same
  historical sample.
- The heuristic baseline is an authoring-time review of two live surfaces. Its
  top-line result is **24 findings: 1 catastrophic, 15 major, 6 minor, and 2
  advisory**, plus **5 recorded passes**. It can show that a structural defect
  was removed; it cannot establish that a reader understood or completed a task.

For M1 through M5 and M7, run the current-surface session before launch if an
improvement claim is required. For M10 through M13, the first measured cohort
becomes a baseline for later cohorts, but it cannot prove that the redesign
improved on an unmeasured prior state. Do not backfill a missing baseline from
memory or substitute a target for one.

## Kill conditions

Each condition names an observation that would make a design decision untenable.

### Lead with the team problem and a whole-model canvas

- **Falsifying observation:** The release-candidate M1 result still has any of
  the three orientation answers absent, or its tested-reader completion does not
  exceed the pre-redesign participant baseline.
- **Response:** Do not ship the above-fold composition as the orientation
  answer. Reduce or rewrite it around the failed answer before restoring detail.

### Nest the work lifecycle inside the cohort-adoption lifecycle

- **Falsifying observation:** In M2, readers describe the work steps as the team
  adoption stages, describe the team stages as work gates, or cannot say which
  lifecycle contains the other after seeing the canvas.
- **Response:** Stop using subordination as the teaching model. Test the
  better-evidenced collapse route: one primary lifecycle, with the other moved
  to a separate explanation rather than shown as a nested peer.

### Limit the canvas to two disclosure levels

- **Falsifying observation:** In the same M2 result, item 3 about the outer team
  spine is `correct` while item 1 about the nested work sequence is `partial` or
  `absent` after the reader used the canvas.
- **Response:** Remove nested detail from the acquisition surface and route it to
  documentation. Do not add a third disclosure level.

### Use one canvas for four audiences

- **Falsifying observation:** M4 shows a role-linked failure: a tested engineer,
  platform lead, or budget holder scores `absent` on the item that represents
  that role's central question while champions can answer it from the same
  artifact.
- **Response:** Keep a shared model only if useful, but add role-specific proof
  or collateral for the failed audience instead of claiming one artifact is
  sufficient.

### Express the tracker as a one-way outbound relationship

- **Falsifying observation:** A next-cohort participant answers M3 item 4 by
  making Jira or Linear the system's source of truth, or expects the tracker to
  write state back into this system.
- **Response:** Treat the geometry as failed. Add direct prose at the point of
  the relationship and retest the same item.

### Teach human decisions and refusal boundaries

- **Falsifying observation:** A participant marks item 2 or 5 `absent`, or says
  the system can approve, merge, or ship on its own.
- **Response:** Replace abstract gate language with the exact human question and
  put the refusal beside the relevant action. Retest items 2 and 5 separately.

### Use three checkable artifacts as proof

- **Falsifying observation:** In M5, a reader cannot locate and correctly
  interpret the artifact for any load-bearing claim, even though it is present.
- **Response:** Remove that artifact from the proof band or pair it with a plain
  statement of what it proves. If safe, current evidence cannot be shown, state
  the evidence boundary instead of substituting an example.

### Treat the pasted-link unfurl as the transfer surface

- **Falsifying observation:** The champion interview's question 13 identifies a
  different repeated transfer artifact, or recipients cannot state what the
  link is, who it is for, and its time cost from the unfurl alone.
- **Response:** Make the observed transfer artifact primary. Keep the unfurl as
  transport metadata, not as evidence that understanding transferred.

### Lead the guides index with ordered paths and a start-here route

- **Falsifying observation:** A platform lead cannot complete M7 without
  champion or facilitator help, cannot name the first result, or reaches a dead
  end before the handoff.
- **Response:** The champion is still a dependency. Repair the missing path
  step; if the roughly one-hour first path is the stop, split out the documented
  20-minute first-value on-ramp.

### Make documentation search-first and group navigation by job

- **Falsifying observation:** In the M7 walkthrough, a platform lead who knows
  the adoption job but no pack name cannot reach the adopt path without help, or
  chooses the wrong destination because the same guide appears to belong under
  more than one job.
- **Response:** Restore one clear canonical placement for ambiguous areas and
  use the index paths to bridge jobs. Do not claim search resolution improved
  while M9 remains unavailable.

### Keep install as the primary marketing action while aiming at a cohort

- **Falsifying observation:** Self-serve M10 meets its under-one-hour target, but
  enterprise rollout misses the under-two-week TTFV target or M11 activation is
  80 percent or lower. That result shows personal proof is not crossing into
  cohort adoption.
- **Response:** Stop treating the install action as the best bridge to rollout.
  Promote the adopt path and cohort cost or ownership information, then measure
  the next cohort separately.

### Treat `workspace-status` as the embedding habit

- **Falsifying observation:** M13 exceeds 70 percent at week 4 while M12 is 70
  percent or lower, or M13 stays at or below 70 percent while M12 exceeds 70
  percent. Either result breaks the assumed link between the habit and
  persistence.
- **Response:** Stop using session-start habit as the retention proxy. Keep M12
  as the outcome and investigate the actual persistence or reversion condition
  with cohort interviews.

## What this plan cannot measure

### Gaps that could be closed with effort

- **Published-site journeys and search resolution.** M9 is unavailable because
  the deployed site has no instrument. Site instrumentation could close the gap,
  but proposing analytics tooling, tags, events, or dashboards is outside this
  plan.
- **Whether subordination improves comprehension.** A pre-redesign and
  post-redesign M2 comparison can answer this locally. Until the pre-redesign
  check runs, the plan has no improvement baseline.
- **Which champion artifact earns funded adoption.** Independent research across
  real decisions could compare the canvas with role-specific collateral. The
  located practitioner sources cannot answer it because they share sales
  incentives.
- **How many process models a reader can sustain.** Primary comprehension
  research could test it. The current two-level disclosure ceiling concerns
  depth, not the number of simultaneous models.
- **Whether the canvas survives GitHub sanitisation.** A real README probe can
  answer this at build handoff. It is a conformance check, not an adoption or
  comprehension outcome, so it is not promoted to a success measure here.
- **Population-level emotions and pains.** Interviews can gather reported
  experience from sampled people. Traffic paths cannot establish why anyone felt
  or acted as they did.

### Questions that cannot be answered as stated

- **Whether the observed Teams referrals were champion transfer.** The API
  records a referrer and count, never intent. An interview can identify one
  person's action but cannot recover intent for all 12 unique visitors.
- **Whether adoption would have persisted without the redesign or another
  intervention.** That counterfactual did not occur. Retention can describe what
  happened, not what the same cohort would have done in an unrealised history.
- **Whether collapse or subordination is universally correct.** The choice
  turns on whether this product's two lifecycles are genuinely orthogonal. Local
  comprehension failures can falsify this design, but external evidence cannot
  settle the product judgement in principle.

## Comprehension check for the next cohort

Use the same five questions as the pre-redesign champion interview so the words
do not move between readings. Ask from memory and keep each answer verbatim.

1. What happens to a single piece of work, from the moment someone has an idea
   to the moment it is running in production? Name the steps in order.
2. At which points does a human have to make a decision, and what is each
   decision actually about?
3. What changes for a team as it takes this on, from first look to it being the
   normal way the team works?
4. If your team already uses Jira or Linear, what is the relationship between
   that tool and this system? Which one is the source of truth?
5. What does this system refuse to do on its own, no matter how it is configured?

Administer the check to somebody the champion onboarded, not only to the
champion. For the marketing-home measure, keep a separate subset of first-time
readers who saw only that page. Record role and exposure so the two conditions
are not blended into one score.

Score each answer `correct`, `partial`, or `absent`, and report the count of
fully correct answers out of five. Judge the idea expressed, not recall of a
gate code. A reader who says a person approves the plan before code is written
has understood the decision.

This method adapts healthcare teach-back. No academic or practitioner precedent
for software-rollout comprehension was located. Healthcare teach-back is
administered by a trained practitioner; this self-serve check is not. Its result
is an experimental signal about these materials, not a validated software
comprehension scale.
