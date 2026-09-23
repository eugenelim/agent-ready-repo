# Verification ledger — changelog fragment assembly measurement spike

Execution observations for run `0a4e62f5-d75d-46dc-8fd1-d5e9a9c90dbb`. The
approved `spec.md` and `plan.md` retain obligations only; everything an
execution observed lands here.

## Run identity

- **Base:** `93bf9cc9e`. `docs/product/changelog.md` and `tools/build-site.py`
  are byte-identical at this commit and in the worktree throughout the run, so
  every measurement shares one base.
- **Engine:** run initialised `--mode code` after an owner-authorized
  `loop-cohort reset` + `loop-engine reset` pair retired a finished spec-plan
  run (`0e32d4dd-65ef-469f-add9-1768b80c7e0b`, state `DONE`).
- **Waves as scheduled:** wave 1 = T1, T2; wave 2 = T3, T4; wave 3 = T5.

## Deviations from a task row's literal method

- **T4 clone base and corpus size, amended pre-seal.** The plan pinned
  `5b379c51f` and 2,910 fragments in T3's and T4's `Tests:` fields. An owner-
  authorized rebase onto `origin/main` rewrote that commit — it is reachable only
  through the reflog and is not on the branch — and moved the free-standing
  released-entry count from 291 to 292. Both values were corrected to `93bf9cc9e`
  and 2,920 before `loop-cohort approve-plan` recorded this run's baseline, so no
  controlled amendment was owed. Recorded in the plan's Changelog.
- **Base-freshness check was red at run start and resolved mid-run.** The first
  `check-base-freshness.py` call exited 1 (one commit behind `origin/main`). The
  owner initially directed holding the base, then directed the rebase; the
  post-rebase call returns `head is current`. `origin/main` had gained a second
  commit by then (`74bcd2e64`, #1415), which is in the run's base.
- **No `implementer` subagent was dispatched.** All five tasks ran in-session.
  The owner directed this, so each of the five `dispatch-receipt` records carries
  `--decline human-directed`. Reason: this spec's evidence of record is retained
  stdout, and an implementer returns a prose status report from which verbatim
  stdout cannot be quoted. T4 also deletes a disposable clone.

## Observations that bound a figure — SUPERSEDED at round 3

> The attribution arithmetic in the first bullet below (+5.22s attributable,
> +12.66s remainder, the docs phase as a negative control) was **withdrawn**
> in review round 3 and no longer appears in the report. `make site-build`
> runs the docs phase after the treatment-dependent web phase in one
> invocation, so identical input does not make it treatment-free. This
> section is retained as the historical record of what was believed at the
> time; the current position is in *Review round 3* below.

- **T4's whole-build metric cannot resolve its own threshold.** The docs-site
  build receives identical input in both arms (264 pages either way) and still
  shows a +3.49s median arm difference, spanning 6.86s to 18.20s across the ten
  retained runs — a range of 11.34s. Of the +17.88s total median difference, only
  +5.22s falls in the web phase, whose input actually changed. The recorded
  +66.08% is directionally safe (every fragment run exceeded the control median,
  and the miss is 6.6x the bar) but is not precise to two figures. Owner directed
  recording the figure with this bound stated rather than re-running.
- **T3's historical-anchor arm is structural, not empirical.** The baseline is
  parsed once and fragment anchors derive from fragment identity, so nothing can
  re-run `_Slugger` over history: the arm cannot fail in this model. The 0-of-157
  figure confirms the model has the claimed structure. The arm that could fail —
  the monolith counterfactual — was not run and is routed to the report's
  "did not measure" section and the delivery spec.
- **T3's zero-fragment parity is partly true by construction.** The model builds
  the historical half by calling the shipping `_project_parsed`, so the arm
  establishes that merge, re-sort and re-serialization change nothing; it does
  not independently re-derive the payload. Stated in the report.
- **Scout runs are not measurements.** A first cold-cache control build took
  75.2s and a subsequent fragment build 53.2s — the fragment arm apparently
  faster. This is the monotonic warm-up drift the interleaved design and the
  discarded per-arm warm-up exist to remove, and neither scout figure is quoted.

## Mutation and control arms observed to fail as designed

- **T2 mutation arm:** removing the canonical sort produced 5 distinct digests
  across the 5 shuffled enumerations, against 1 with the sort present. The arm
  fails when the invariant is removed.
- **T2 shuffle validity:** 5 of 5 enumeration orders were distinct, so the single
  canonical digest is a property of the sort and not of an unvaried input.
- **T1 control arm:** 190 of 190 monolith pairs conflicted, against 0 of 190 in
  the fragment arm.
- **T1 classifier self-check:** the known-conflicting pair bucketed to exit 1 and
  the known-clean pair to exit 0, before either arm's figure was taken.
- **T4 wiring proof:** before timing, the fragment arm's generated payload
  carried 3,077 groups and 3,201 bullets against the control's 157 and 281,
  confirming the timed path reaches the staged corpus rather than ignoring it.

## Disposal

- The disposable clone (1.0G) was deleted before the build-cost figure was
  recorded in the report. The four retained stdout captures and twelve build logs
  survive in the session scratchpad.
- The assembler prototype and the timing harness lived outside the repository and
  are reconstructed from the report rather than maintained.
- This worktree's `git status --porcelain` was empty before the run, after T1,
  and after the clone's deletion.

## Open assumptions, settled by the owner on reading the run

- **§ 7's "ten times the current release-entry count" reads as 11.0x.** 2,920
  fragments staged on top of 292 free-standing entries totals 3,212 — ten times
  the current count *added*, the more demanding of the two readings. Settled by
  the owner during the run; recorded in the report's measurement 4.
- **The synthetic corpus is fair for page count, weak for parse cost.** ~330-byte
  fragments with one bullet each model group and page counts faithfully and
  understate per-fragment read and parse cost. The understatement falls on the
  phase the decomposition showed was not the cost driver. Settled by the owner;
  recorded as a stated limit in the report.

## Review round 1 — adversarial-reviewer, adjudicated

Six source findings; four sustained, two refuted on evidence.

**Sustained and repaired:**

- *Figures not traceable to quoted stdout.* The grounding counts, the wiring
  proof, the phase decomposition and the corpus size were retained as run output
  but never quoted in the report, so a reader could not verify them. All four are
  now fenced blocks in the sections that use them.
- *The anchor list was absent.* AC 6 names the anchor list as a diagnostic; the
  report carried only the first anchor, the last, and a digest. All 157 anchors
  are now recorded in payload order.
- *The precision bound was arithmetically and methodologically unsound.* The
  report claimed a +12.66s unattributed remainder sat "inside" an 11.34s range —
  12.66 is larger than 11.34 — and treated one identical-input phase's spread as
  an error bar for the whole build. Both are wrong. The section now reports
  +66.08% as an observed point estimate, states that five runs per arm at this
  dispersion support no valid uncertainty bound, records that the two samples
  overlap (21 of 25 run pairs favour the fragment arm; the largest control run
  exceeds four of five fragment runs), and makes no directional-certainty claim.
- *The method misattributed an import.* The report said both artifacts import
  `tools/build-site.py`. Only the prototype does; the tracked script is standard
  library plus Git. Corrected.

**Refuted, not repaired:**

- *AC 10 ticked despite the threshold miss.* Refuted on the spec's own text, not
  on owner authority: all sixteen criteria share the grammar "records X; the
  figure is Y, per § 7 Z", and the spec separately requires a survive-or-kill
  verdict per measurement, excludes build cost from the aggregation, and
  prescribes the above-bar follow-on in Durable Outputs. A checked AC 10 records
  completion of the measurement obligation, not attainment of the threshold. The
  scope owner had independently reached the same reading during the run.
- *`main()` exits 0 when the error bucket is non-empty.* Refuted on authority:
  AC 3 requires per-arm error counts and classifies a non-zero count as harness
  failure, but requires no non-zero process exit, and the script already reports
  errors in a distinct bucket rather than folding them into the clean count.
  Left unchanged; it would be a behaviour change outside the accepted intent.

## Defect found by the controller, not by a reviewer

`tools/measure-changelog-fragment-merges.py` hardcoded its monolith insertion
anchor as the literal `## [core]`. Twenty-four distinct packages appear as
release headings and only 139 of 292 are `core`, so a future base whose newest
entry is another package would have sent the control arm's insertion further
down the file — measuring a shape no release takes, and reporting it as a clean
result. Replaced with a regular expression matching any `## [pkg][version]`
heading, which resolves to 292 headings and correctly skips `## [Unreleased]`.
The insertion point is unchanged at this base, and T1 was re-run after the fix:
both arms reproduce 0 of 190 and 190 of 190 with empty error buckets.

## Review round 2 — adversarial-reviewer, adjudicated

Three source findings; all three sustained, none refuted.

- *Two empirical counts were inaccurate or untraceable.* The report placed
  #1415 three commits before the base when it is two (`93bf9cc9e~2` is
  `74bcd2e64`), and cited "four `[Unreleased]` groups" with no quoted source.
  The commit count is corrected. The `[Unreleased]` count is dropped rather than
  cited: it happens to be true at this base, but it carried no weight in the
  sentence and the spike never measured it.
- *The build-cost conclusions still exceeded what the data attributes.* Having
  conceded that five overlapping runs support no confidence claim, the report
  then called the cost large, attributed it to page generation, and called
  per-page cost low — while only +5.22s of the +17.88s difference sits in the
  changed-input phase and +12.66s is unattributed. The section is rewritten to
  separate two things that had been conflated: the page counts (3,282 against
  216) and the `getStaticPaths` mechanism are structural facts from code and the
  retained logs, whereas "page generation is what makes the fragment build
  slower" is now labelled an untested hypothesis for the delivery spec to price.
  The verdict prose and the closing recommendation were corrected the same way.
- *The control arm re-derived the parser's release-heading contract.* The
  regex introduced in round 1 had zero false positives on this file — 292 hits,
  all real level-2 headings, identical heading text, and no fence markers before
  the first at line 67 — but it implemented no fence or comment state machine
  and admitted identities the parser rejects, such as `[Unreleased][unreleased]`
  or an undated entry. `ParsedChangelog.headings` is exported precisely so a
  caller needing heading position does not re-derive that machine. The script
  now imports `tools/build-site.py` by path, takes the first free-standing
  released entry from `parse_changelog_releases`, and resolves its level-2
  heading position from the exported index, raising when the parser rejects the
  candidate. The resolved position is unchanged at this base (line 67), and T1
  re-run after the change reproduces 0 of 190 and 190 of 190 with empty error
  buckets.

That last repair reversed part of round 1's fix: the report had just been
corrected to say the measurement script imports nothing from this repository,
which the change made false. The method section now states what each artifact
takes from `build-site.py` and why.

## Review round 3 — adversarial-reviewer, adjudicated

Three source findings; two sustained, one refuted.

- *An unquoted commit-distance figure.* "Two commits before this base" was
  correct but established by no quoted run, and the traceability rule does not
  exempt a correct repository fact. The count is removed; the `#1415`
  provenance link stays, which is what the sentence needed.
- *The phase decomposition assigned cause the run did not isolate.* This is the
  substantive one, and it defeats an argument the controller had relied on since
  round 1. The report treated the docs-site phase as a negative control because
  its input is identical in both arms. `make site-build` runs the web build and
  then the docs-site build in one invocation, so the docs phase executes after a
  web phase that produced fifteen times more pages in the fragment arm; it
  inherits page cache, memory pressure and thermal state from the treatment and
  is therefore not treatment-free. Subtracting independently computed medians
  would not yield a valid split even if the phases were independent. Every
  "unaffected phase", "noise", "attributable", "remainder" and "cost driver"
  claim is removed. The per-phase timings are re-derived and recorded as bare
  observations with their ranges, under an explicit statement that they are not
  components, and the retained stdout was regenerated to match so that no
  quoted block still carries the attribution arithmetic.

**Refuted:** the prototype's fifth `heading` envelope field. The plan's Design
calls its four fields "the minimum that lets T3 answer the anchor question", so
exceeding the minimum contradicts neither that text nor the pinned `Touches`,
`Tests` or `Done when` fields, and is not an execution deviation.

## What three review rounds have and have not moved

No measured result changed in any round. Both arms of T1 held at 0 of 190 and
190 of 190 across three re-runs and two rewrites of the insertion-anchor code;
T2 held at 1 digest against 5; T3 held at byte-identical parity, 20 of 20, and
0 of 157; T4's durations were never re-run. Every sustained finding across all
three rounds was a claim layered on top of those numbers rather than a defect in
them — first a precision bound, then a causal attribution, then the phase
decomposition that the attribution rested on. The measurements were sound and
the prose around them was repeatedly not.

## Review round 4 — two lanes, adjudicated

The quality lane was added as a stated discretionary second reviewer, not by
the high-risk trigger: this change is not structural and warrants no
operational-safety module, but the tracked script is a Durable Output whose
closeout condition is reproducing the report's counts from a clean checkout,
and that lens is not adversarial review's. It found four defects the three
adversarial rounds had not.

**Adversarial — four sustained, none refuted.**

- The T1 counts were quoted from a run at one commit while the prose assigned
  them to the report's base. No run at that base is retained, so the cross-base
  equality claim is removed and measurement 1 now names its own base.
- "Understates per-fragment read and parse cost" asserted a direction the run
  never measured. The byte-volume mismatch is the measured fact; the effect on
  read and parse cost is now recorded as unknown in direction and size.
- `first_release_line` resolved the insertion anchor by matching heading TEXT.
  `changelog.md` contains two duplicate level-2 titles, including
  `[core][2.3.0] — 2026-08-07` — the pair the parser's slugger docstring cites —
  so a duplicate could redirect the anchor to an occurrence the selected release
  does not sit at. This was a defect introduced by the round-3 repair. Selection
  is now by source position plus the parser's own release-identity predicate,
  which cannot pick a different occurrence, and it fails closed if that
  predicate is unavailable.
- The interleaving rationale claimed page cache, warm-up and thermal state
  drift *monotonically*. Nothing measured them. Interleaving is now justified
  against time-order effects of any shape.

**Quality — three sustained, two refuted.**

- Git subprocesses inherited redirect variables and an ambient identity, so an
  inherited `GIT_DIR` made `-C` cosmetic and `commit-tree` would fail on a
  machine with no configured identity. Every invocation now runs under a
  controlled environment that strips the redirect variables and supplies a
  process-local synthetic identity and fixed timestamps. The reader's git
  configuration is not touched.
- **The run deposited unreachable objects in the shared object store.** This is
  a worktree, so `.git` redirects to the parent repository: `hash-object -w`,
  `commit-tree` and `merge-tree --write-tree` were writing into
  `/Users/.../agent-ready-repo/.git/objects`, a tree the measurement never
  touched, and `git status --porcelain` cannot reveal it — so the recorded
  worktree-cleanliness evidence was true but incomplete. Objects now go to a
  temporary directory with the real store as a read-only alternate. Measured
  before and after a full run: loose-object count in the shared store 8,297
  before and 8,297 after, a delta of zero.
- `ArmResult.commits` was populated and never read. Removed.

**Refuted:** that the procedure cannot replay its recorded fixture because it
binds to `HEAD` — the retained output records the exact run commit, so a later
run is distinguishable, and the controller's original decision not to add a
`--base` flag stands. And that `merge_tree` should preserve stderr and pair
identity — § 7 assigns Failure diagnosability to the delivery spec, and this
spike owes only the per-arm error counts. The owner separately bounded that one
out of scope.

T1 was re-run after every code change in this round and reproduces 0 of 190 and
190 of 190 with empty error buckets; the anchor still resolves to line 67.

## Review round 5 — quality lane clean, adversarial four sustained

**Quality lane: `Clean — ready to commit.`** after one repair round. Recorded
with `--structural-clean-file`, not `--direct-clean-file`: the persisted report
differs from the sentinel by one trailing newline, which is exactly the
difference the structural form exists for. Its four round-1 findings were the
highest-value of the whole review, and the shared-object-store defect in
particular survived five adversarial passes unnoticed.

**Adversarial: four sustained, none refuted.** Three were the same over-claim
class as every earlier round, and the fourth was a defect in the controller's
own reasoning.

- Measurement 1 named two bases: the method said the branches were built from
  the header's base while the retained run and the qualifying note said
  otherwise. Every statement in that section now names `443f141f2`, and the
  header states plainly that the report has no single base — measurements 2, 3
  and 4 at `93bf9cc9e`, measurement 1 at its own, each figure beside the base
  its run names.
- The parse-cost bullet still said the run "understates per-fragment read and
  parse cost" one sentence before conceding the effect was unknown. The
  byte-volume mismatch is what was measured; the read and parse effect is now
  recorded as unknown in direction and size, full stop.
- The interleaving rationale claimed protection against time-order effects "of
  any shape". Every retained pair runs control before fragment, so an
  alternating effect or one acting within a pair stays aligned with the
  fragment arm. The claim is now bounded to the gradual trend this ordering
  actually mitigates, and says what it does not catch.
- **`first_release_line` tested heading level, which is not the parser's
  free-standing test.** The controller had argued that a level-2 release
  heading is free-standing by construction because `## [Unreleased]` is itself
  level 2. That argument is unsound: the parser derives `unreleased` from the
  whole stack of enclosing headings, independent of depth, so a level-1
  Unreleased region can enclose a level-2 release. It held on this file only by
  accident of layout. The function now zips release-bearing headings against
  release records — 351 each, equal titles, verified in source order — and
  returns the position of the first record whose `unreleased` flag is false,
  raising if the two sequences ever diverge in count or identity.

T1 re-run after the change: 0 of 190 and 190 of 190, empty error buckets,
anchor still at line 67, and the shared object store measured 8,309 loose
objects before and 8,309 after.

## Review round 6 — one finding, adjudication indeterminate, owner-directed fix

The adversarial lane returned a single finding: the report said the synthetic
corpus "understates byte volume by design" and "badly", while the retained
evidence compares 812,466 synthetic bytes only against the current
598,239-byte monolith and never measures what a realistic future fragment body
weighs. The observation is correct.

Adjudication returned the indeterminate stop signal rather than a verdict. It
agreed the claims are unsupported but held that the severity downgrade from
blocker to advisory is an owner decision, on the grounds that both cited
locations are working material.

**The controller disagrees with that ground and records the disagreement.** The
spec's tier note classifies sections of the *spec* — `Outcome`, `What Changes`,
`Durable Outputs`, `Follow-ons`, `Assumptions`. The flagged text is in the
research report, which that note does not govern. The report answers to the
spec's `Agent Rules`, which the same note names as contract, and whose Never-do
rule forbids reporting what the retained stdout does not contain. On that
reading the finding blocks. The disagreement changes no action: the neutral
wording is more accurate either way.

Disposition: the scope owner directed the correction. Because adjudication
produced no sustained findings, no findings round was recorded and the retry-cap
override the owner had authorised was not consumed; `review_retry_count` stays
at 5 of 5. The text now records the measured comparison against today's
monolith, states that the corpus's relationship to realistic fragment bodies
was not measured, and claims no direction in either place.

## The one defect class this review found

Across seven adversarial rounds and two quality rounds, twenty findings were
sustained by adjudication and five refuted, plus one more repaired under owner
direction when round 6's adjudication returned the indeterminate stop signal
and so produced no sustained entry — twenty-one repairs in all. Every sustained adversarial finding was one class: a
claim reaching past its evidence. Sustained counts per adversarial round ran
4, 3, 2, 4, 4, 1. The measurements never moved — T1 held at 0 of 190 and 190 of
190 through five re-runs and four rewrites of its insertion-anchor code, T2 at
1 digest against 5, T3 at byte-identical parity with 20 of 20 and 0 of 157, and
T4's durations were never re-run. What kept failing was the prose around the
numbers, and twice the controller's own reasoning about them: the docs-site
phase as a negative control, and heading level as a free-standing test.

The quality lane, added as a discretionary second reviewer rather than a
triggered one, closed clean after a single repair round and found the four
defects that mattered most to the tracked script — including that every run had
been depositing unreachable objects in the parent repository's shared object
store while `git status --porcelain` reported the worktree clean.
