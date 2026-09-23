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

## Observations that bound a figure

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
