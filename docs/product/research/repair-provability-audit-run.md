# Repair provability audit — first run: the instrumentation gate does not pass

- **Run date:** 2026-09-17
- **Owner:** eugenelim, Platform Core maintainer
- **Against:** `origin/main` at `9d430418b`
- **Verdict:** the gate **failed on the first pass** over population selection,
  then passed. A determinate predicate now reproduces the design's strata, and a
  three-case oracle run discriminated semantic from structural kills against
  predicates frozen before execution. **The audit is ready to scale**, subject to
  two harness requirements: revert every mirrored copy of a hunk, and score
  provability per repair rather than per commit. What stands from the first pass:
  the design's stated population criterion does not decide the same set twice and
  its own frozen corpus contradicts its prose, so the population must be frozen
  on an explicit predicate. **The rate is still unmeasured** — three hand-picked
  cases span the outcome space and do not estimate a frequency.
- **Cost:** zero model calls for the measurement itself; one subagent call for
  the independent hand result. No repository code was executed and no commit was
  reverted.

Feeds the accepted
[work-loop delivery efficiency](../intents/work-loop-delivery-efficiency.md)
intent, whose § Projection ranks this audit first.

## What this run did and did not do

The design puts a gate upstream of the measurement: *"A 10-case instrumentation
audit passes before scaling to all 113."* This run reached that gate and stopped
there, because it failed.

- **Done:** reconstructed the population from git metadata, classified strata,
  drew ten cases deterministically, and compared the harness classification
  against an independent hand classification.
- **Not done:** no repair was reverted, no oracle was run, and no
  semantic-kill / structural-kill / survives / unmeasurable outcome was recorded
  for any case. **The audit's actual question — how often a shipped repair has a
  control that would fail if the repair were reversed — remains unanswered.**

## Finding 1 — "repair event" does not decide the same set twice

The design defines the population as commits answering one adjudicated review
round, and asserts the round is recorded durably in the commit message: *"the
sustained and refuted counts, each finding's severity band, the adjudicated
mechanism, and the remedy applied."*

Two readers applied that sentence to the same ten commits.

| Reader | Reading | Admitted |
| --- | --- | ---: |
| Harness | the message carries adjudication vocabulary in a review context | **10 of 10** |
| Independent hand check | the four listed elements are *required* | **1 of 10** |

That is not a tie-breakable disagreement. It is the full range of the criterion.

**The strict reading is refuted by the design's own corpus.** The design takes
its selection method from the
[focused re-review spike](work-loop-focused-re-review-spike.md), whose four
frozen cases are the only worked examples of a "repair event" in the
repository. Applying the strict reading to them:

| Case | Repaired revision | `N sustained` | `N refuted` | Severity bands | Strict verdict |
| --- | --- | :---: | :---: | :---: | --- |
| F1 | `ab6016abe` | yes | yes | yes | **admitted** |
| F2 | `27693afb5` | no | no | no | rejected |
| F3 | `af84562eb` | no | no | no | rejected |
| F4 | `1423734b6` | no | no | no | rejected |

**One of the four cases the design cites as its method survives the design's own
stated requirement.** F3's message opens `Verdict was GUARD STILL HOLLOW` and
F4's opens `Both reviewers independently caught the same two defects` — real
adjudicated repairs that record no counts and no severity bands.

So the design's prose overstates what the corpus records. Neither reader is
wrong, which means the population is not a determinate object and no count drawn
from it is reproducible. This is the audit's own target failure class — an
artifact asserting something that cannot be checked — occurring in the
instrument rather than in the corpus it was built to measure.

## Finding 2 — the total roughly reproduces; the strata do not

Reconstructed with the loosest defensible marker (`sustained|refuted` anywhere
in a non-merge commit message on `origin/main`, author date on or before
2026-09-11), then filtered to a provable base:

- 130 candidates
- **104 with a provable base**, against the design's **113**

The total is within 8%. The strata are not:

| Stratum | This run | Share | Design | Share | Oracle the stratum implies |
| --- | ---: | ---: | ---: | ---: | --- |
| source + test | **21** | 20.2% | **39** | 34.5% | revert source, observe co-changed test |
| source only | 18 | 17.3% | 21 | 18.6% | revert, run pre-existing affected tests |
| docs only | **46** | 44.2% | **28** | 24.8% | before/after predicate, self-tested |
| test only | 19 | 18.3% | 25 | 22.1% | classify by finding intent first |
| **total** | **104** | | **113** | | |

`source + test` is the audit's headline feasibility claim — *"yields 39 cases
with an executable oracle"*. This run reproduces 21. The cheapest, most
decisive stratum is roughly half the advertised size, and the most
judgement-heavy one is 64% larger.

## Finding 3 — the design states no path-classification rule, and the strata swing on it

The design says strata are *"classified from git metadata alone, no execution"*
but never says what counts as source, test or docs. Holding the population fixed
at 112 candidates and varying only that rule:

| Path rule | source+test | source only | docs only | test only |
| --- | ---: | ---: | ---: | ---: |
| `tests/` dirs + `test_*.py` + fixtures as test; config counts as source | 30 | 20 | 43 | 19 |
| same, fixtures not test | 30 | 20 | 43 | 19 |
| source restricted to `.py/.ts/.js/.sh` | 16 | 10 | 52 | 33 |
| as above, `tools/test_*` also test | 16 | 10 | 52 | 33 |
| **design target** | **39** | **21** | **28** | **25** |

`source+test` moves by a factor of 1.9 across four rules a careful reader might
each pick, and none of them reaches 39. Because every stratum carries a
*different* oracle, an unstated path rule is not a presentational gap — it
decides how many cases are cheaply measurable.

The independent hand check chose a fifth rule again: shipped agent instructions
(`SKILL.md`) count as source, `workspace.toml` counts as planning metadata
rather than source. Both are reasonable; neither is derivable from the design.

## Finding 4 — strata agree case by case, so the aggregate gap is selection

Harness and hand agreed on the stratum for **9 of 10** cases, disagreeing only on
`9b957d246` (whether `workspace.toml` is source or planning metadata). Per-case
path classification is therefore largely reproducible, and the aggregate
divergence in Finding 2 is dominated by *which commits enter the population*,
not by how their paths are read. Fixing the path rule alone would not fix the
counts.

## Finding 5 — the base rule presupposes a merge workflow this repository mostly does not use

The design inherits `B = git merge-base M^1 M^2` for the merge `M` that landed
the branch. That requires a merge commit to exist.

Measured on `origin/main` at `9d430418b`: of **1,299** first-parent commits,
**340** are merges. **959 — 73.8% — landed with no merge commit at all**, by
squash merge or direct commit. Fourteen of the 130 candidates are themselves
such commits, and under the design's own rule they have no base and therefore no
`B..R` whole-change subject.

This is not fatal to the audit, but it silently removes cases and it biases the
population toward the era and the branches that used true merges. A squash-merge
base rule has to be stated before the population can be frozen.

## Finding 6 — the harness's own base computation was wrong, and the gate is what caught it

Recorded because the audit exists to measure exactly this class, and because a
run that hid its own instrument defect would be the failure it is studying.

The first implementation resolved the landing merge as *the earliest first-parent
merge whose second parent contains R*. A commit already on `main` is an ancestor
of every later branch, so for such commits the rule returned an unrelated later
merge. On `613739e65` it produced a base **equal to R itself**, making `B..R`
empty — a case that would have been measured as though it had a whole-change
subject when it had none.

The corrected rule requires `R` to be reachable from `M` **and not** an ancestor
of `M^1`. Correcting it moved the population from 112 to 104. The defect was
invisible in the aggregate and surfaced only when the ten drawn cases were
inspected individually, which is the argument for the gate the design already
specifies.

## Erratum, same day: a determinate predicate exists, and it largely reproduces the strata

Findings 1 to 3 above were measured against **one** candidate predicate — the
design's own `sustained|refuted` vocabulary, here called **P0**. A second round
labelled a larger sample semantically and scored four predicates against it.
That round **overturns Finding 2's conclusion** and narrows Finding 1.

**Ground truth.** An independent reader labelled 55 commits on one question —
is this a natural repair commit answering an adjudicated review round against
its own branch's work? — with message format explicitly excluded from the test.
Thirty were drawn from P0's selection, ten were `fix()`-typed review-mentioning
commits P0 **misses** (to expose false negatives), and fifteen were drawn from
the region a wider predicate newly admits.

| Predicate | Definition | Selected | Precision | Recall |
| --- | --- | ---: | ---: | ---: |
| **P0** | `sustained\|refuted` in the message | 104 | ~77% | ~77% |
| **P1** | P0, and the commit type is not `feat` | — | ~86% | ~77% |
| **P2** | wider review vocabulary, type not `feat` | 265 | ~69% | ~94% |
| **P3** | P2, and a repair verb in the subject | **147** | **~95%** | ~65% |

P2's precision fell to 60% on the 167 commits it newly admits, which is why its
overall figure is worse than P0's despite better recall. Precision and recall
here are measured on the sampled regions, not on each predicate's whole
selection.

**P3 largely reproduces the design's strata:**

| Stratum | P3 | share | Design | share |
| --- | ---: | ---: | ---: | ---: |
| source + test | 53 | 36.1% | 39 | 34.5% |
| source only | 27 | 18.4% | 21 | 18.6% |
| docs only | 30 | 20.4% | 28 | 24.8% |
| test only | 37 | 25.2% | 25 | 22.1% |
| total | 147 | | 113 | |

All four shares land within 4.4 points. **Finding 2's claim that the strata do
not reproduce is therefore withdrawn:** they do not reproduce from the marker
the design *states*, and Finding 3's point stands that the path rule is
unstated, but a determinate predicate reproducing the design's proportions
exists. `source + test` comes out at 53 rather than 39, above the design's
figure rather than half of it. The residual gap is most likely the history
window, since this run cuts at 2026-09-11 while the design was written on
2026-09-10.

**What Finding 1 still says.** The design's prose remains wrong about what the
corpus records — three of its four frozen cases carry no counts and no severity
bands, and a reader who treats that sentence as a requirement admits 1 case in
10. Determinacy was never the hard part; a regex is determinate. Validity was,
and it is now measured rather than asserted.

**Remaining step before freezing P3.** Its ~95% precision rests on 21 selected
cases falling inside the sampled regions. A confirmatory sample drawn from P3's
own 147 would close that gap. Nothing else blocks freezing the population.

## P3 confirmed on its own selection, and the oracle phase scoped

Two independent workers, one per task.

### P3's precision on a fresh draw from its own 147: 14 of 16

The erratum's ~95% figure rested on 21 cases that happened to fall inside
regions sampled for other predicates. A confirmatory sample of **16 commits
drawn from P3's own selection**, none previously labelled, spread across all
four strata (5 source+test, 4 source only, 4 test only, 3 docs only), returns
**14 yes / 2 no — 87.5% precision**.

That is lower than 95% and it is the figure to carry. On a sample of 16 the
interval is wide, so treat 87.5% as a point estimate, not a tight bound.
Applied to the population: 147 selected, **roughly 129 true repair events**,
against the design's 113.

The two false positives name their own classes, and both are excludable if
precision needs to rise:

| Commit | Why it is not a repair event |
| --- | --- |
| `bd7d9030b` | fixes a self-found guard defect before the next review — no review round to answer |
| `de6d4aac0` | reconciles backlog lifecycle state against already-completed work |

**P3 is fit to freeze as the population predicate.** It is determinate, it
reproduces the design's strata shares within 4.4 points, and its precision is
now measured on its own selection rather than inferred from a neighbouring one.

### The oracle phase costs adjudication, not compute

Five `source + test` cases were scoped without running anything. The result
corrects a cost assumption this run recorded earlier.

**The environment is cheap.** None of the five needs an editable install, a
build step or generated inputs. Python 3.11+, pytest, git, Bash and PyYAML
cover all five; the tests build their own temporary git repositories. The
expensive part is not reconstructing an environment — it is deciding, per case,
what the adjudicated source repair actually was.

| Case | Estimate | Dominant cost |
| --- | ---: | --- |
| `00df54200` | 25 min | three mirrored copies of the hunk |
| `b1e7d6864` | 20 min | simple revert, but the failure is structural |
| `3546f2c28` | 45 min | compound repair, fixture/source attribution |
| `5ae6efe67` | 50 min | determining whether a semantic oracle exists at all |
| `90cb9426e` | 75 min | two independent repairs, one Windows-only |

About **43 minutes per case**, so **roughly 38 sequential hours for 53 cases**,
with a 30-50 hour band depending on how many commits are compound.

**Three validity threats, ranked by the scoping worker:**

1. **Wrong unit of repair.** A compound commit can carry a controlled defect and
   an uncontrolled one. One failing test then makes the whole commit read as
   controlled. `3546f2c28` and `90cb9426e` both have this shape.
2. **Structural false positives.** Digest pins, changed reason strings, shared
   fixtures and mirrored projections can all fail without exercising the
   dispatched defect.
3. **Historical environment drift.** Python and Bash versions, symlink
   permission and Windows `icacls` can leave R red or silently skip the path.

**A harness requirement found by inspection.** In `00df54200` and `b1e7d6864`
the repaired hunk is byte-identical in three locations — `.agents/skills/`,
`.claude/skills/` and `packs/core/.apm/skills/`. The test exercises the
`packs/core/.apm` copy. **Reverting one copy leaves the tested copy repaired and
scores the case `survives` when the control would in fact have fired.** Any
oracle harness must revert every mirrored copy, and must assert it did.

**A preview of the result, and a caution.** Of the five scoped cases only
`00df54200` and `3546f2c28` look like clean semantic kills. `b1e7d6864`'s
co-changed test fails only on a changed reason string, and `5ae6efe67`'s fails
only on a digest pin — both structural, neither controlling the dispatched
defect. `5ae6efe67` may have no semantic oracle at all. If that ratio holds, the
audit's own thesis is visible before any test runs: the co-changed test
frequently does not control the defect the repair was dispatched against. **That
is a hypothesis from five inspected cases, not a result.**

### Recommended gate before the full 53

Run three, chosen to span the outcome space rather than to confirm the method:
`00df54200` (expected semantic kill, validates mirrored-source handling),
`b1e7d6864` (expected structural kill, tests whether the adjudicator
distinguishes a changed reason string from the defect), `90cb9426e` (compound
repair and platform-specific attribution). Add `3546f2c28` and `5ae6efe67` to
exercise fixture coupling and the `unmeasurable` rule.

## The three-case oracle gate: it passes, and the oracle discriminates

Run 2026-09-17 on the three cases the scoping worker recommended. Protocol, in
this order, with a different worker at each step so no worker judged its own
output:

1. **Worker A froze the closure predicate for each case before anything ran** —
   the dispatched defect, the exact source hunks including every mirror, the test
   invocation, the semantic-kill signature and the structural-only signature.
2. This session executed the reverts in a throwaway detached worktree. The main
   worktree was never touched; the scratch worktree was removed afterwards.
3. **Worker B adjudicated the observations against the frozen predicates**, with
   no authority to write a new predicate to fit a result.

### Outcomes

| Case | Outcome | What decided it |
| --- | --- | --- |
| `00df54200` | **semantic kill** | With all three mirrors reverted, the replay returned 1 because the retry-cap guard refused it after the first record had set the count to 5 — the dispatched defect exactly |
| `b1e7d6864` | **structural kill** | The unsafe input stayed rejected with exit 2; only `reason` changed from `plan_file_is_symlink` to `plan_file_outside_root` |
| `90cb9426e` | **semantic kill** (AST repair) | Reverting the walker made the lint scan the fixture and return 0 findings, so the banned flags went undetected |

`R` passed first in all three cases, at the correct detached revision on a clean
tree, before any reversion.

**The frozen predicates anticipated all three outcomes.** No valid observation
landed outside both signatures. The freeze-before-observe protocol is therefore
cheap and it works, and it is what makes the structural/semantic distinction
decidable rather than arguable after the fact.

### Two harness requirements, now measured rather than predicted

**1. Reverting one mirrored copy manufactures a false survivor.** In
`00df54200` the repaired hunk is byte-identical in `.agents/skills/`,
`.claude/skills/` and `packs/core/.apm/skills/`, and the test exercises the
`packs/core` copy. Reverting only `.agents` was run as a deliberate control arm:
**the test passed.** A harness that reverts one copy would have recorded
`survives` for a repair whose control does in fact fire. The scoping pass
predicted this by inspection; this run confirms it by observation. Any oracle
harness must revert every mirror and assert that it did.

**2. Provability must be scored per repair, not per commit.** In `90cb9426e` a
second, independent repair — Windows ACL matching by SID rather than by English
principal name — was reverted in an additional arm. The failure was
**byte-identical** to the arm that left it intact, so that repair has no control
in this test at all. Scored per commit, the case reads `semantic kill` and the
uncontrolled repair disappears. The design's four outcomes are sound, but its
unit is wrong: a compound commit needs one outcome per adjudicated repair.

### What this does and does not establish

It establishes that the oracle **discriminates**: on three real cases it
separated a genuine control from a changed reason string, and it did so against
predicates written before the results existed. That is the property the
instrumentation gate exists to check, so **the gate passes** and the stratum can
be scaled subject to the two harness requirements above.

It establishes nothing about the rate. Two semantic kills and one structural kill
in three hand-picked cases is not an estimate of how often repairs ship with a
control that can fail — the three were chosen to span the outcome space, which is
the opposite of a random draw. The rate needs the frozen population sampled
without regard to expected outcome.

One early observation of `b1e7d6864` was **void and is excluded**: a
`git checkout` aborted against a dirty tree, so the revert was applied to the
wrong revision. It was detected from the printed `HEAD`, and the case was re-run
from a clean checkout. The clean run produced the same outcome, but the voided
run is recorded because "the checkout silently did not happen" is precisely the
environment-drift threat the scoping pass ranked third.

## What has to change before this audit can run

1. **Adopt P3 as the frozen population predicate** (see the erratum): wider
   review vocabulary, commit type not `feat`, repair verb in the subject. It is
   determinate, **87.5% precise on a fresh draw from its own selection**, and
   reproduces the design's strata shares within 4.4 points. Optionally exclude
   self-found-defect repairs and lifecycle reconciliation, the two false-positive
   classes the confirmatory sample named. Delete the design's claim that the
   round is recorded with counts and severity bands, which its own corpus
   contradicts.
2. **State the source / test / docs rule** as part of the frozen design, not as
   an implementation detail.
3. **State a base rule for squash-merged changes**, which are how roughly three
   quarters of this repository's history landed.
4. **Re-freeze the population and re-run the 10-case gate** after 1 to 3. The
   113 and the 39 in the design should be treated as unreproduced until then.

## Transfer limit on this run

This run measures the *instrument*, not repair provability. It establishes that
the audit as designed cannot yet produce a reproducible population; it says
nothing about how often repairs ship with a control that can fail. The design's
`## What this does not measure` section still stands unchanged, and its
`## Transfer limits` section on the 307 goal-based verification declarations is
untouched by this run.

## Scale-up attempt, 2026-09-17: the oracle reproduces, the population does not

- **Run date:** 2026-09-17, after PR #1353 merged as `f443b09ff`
- **Against:** `origin/main` at `9d430418b`, the same revision the earlier
  sections measure
- **Verdict:** the three-case oracle gate **reproduces exactly** on an
  independently rebuilt harness, and both harness requirements are confirmed a
  second time by observation. **The frozen population does not reproduce.** P3
  is documented above as 147 commits with 53 in `source + test`; the predicate
  as stated selects **164 with 58 in `source + test`**, and no reading of it
  tested here returns 147. So the 50 remaining cases were not drawn, because
  the denominator of the headline rate is not yet a settled object.
- **Cost:** zero model calls. Eight pytest runs in a throwaway detached
  worktree, about 4 minutes of test time. No repository code was changed and no
  commit was reverted outside that worktree, which was removed afterwards.

### The harness is validated on five numbers it reproduces exactly

The harness was rebuilt from scratch, because the first run retained no scripts.
Before trusting it against P3, it was calibrated against every precisely stated
number in the earlier sections. All five reproduce on the nose:

| Claim, as recorded above | Section | Rebuilt harness |
| --- | --- | --- |
| P0 selects **130** candidates | Finding 2 | **130** |
| **14** of the 130 are first-parent-line commits with no base | Finding 5 | **14** |
| **1,299** first-parent commits | Finding 5 | **1,299** |
| **340** of them are merges | Finding 5 | **340** |
| **959** landed with no merge commit | Finding 5 | **959** |

The corrected base rule also turns out to be *unambiguous*, which Finding 6
argued for but did not measure: across all 340 first-parent merges, **no commit
falls inside more than one qualifying merge set**. Every merge-landed commit has
exactly one landing merge, so "earliest qualifying merge" and "the qualifying
merge" name the same thing. That independently confirms Finding 6's correction.

### The base filter above drops 12 commits it does not account for

Finding 2 reports 130 candidates and **104** with a provable base. Finding 5
reports that **14** of those 130 are first-parent-line commits which "have no
base" under the design's rule. Those two statements do not agree: 130 − 14 is
**116**, not 104.

The rebuilt harness returns 116, and the 14 baseless commits it finds are
*exactly* the 14 first-parent-line commits — the two sets are identical, not
merely equal in size. So the arithmetic in Finding 5 reproduces and the headline
104 in Finding 2 does not. Twelve commits were dropped by something the run
does not record.

This matters beyond bookkeeping. The same unrecorded step sits upstream of P3,
so it is the most likely single cause of the 147-versus-164 gap.

### P3's 147 is not reachable from the predicate as stated

The predicate is recorded as: review vocabulary
(`sustained|refuted|adjudicat\w+|re-review|adversarial review|round[- ]\d+|round \w+`),
commit type not `feat`, and a repair verb in the subject
(`repair|close[sd]?|closing|fix(es|ed)?|answer\w*`).

Read faithfully — all seven vocabulary alternatives, case-insensitive, matched
against the whole message, word-bounded, with the corrected base rule — it
selects **164**, not 147:

| | Recorded above | Rebuilt harness |
| --- | ---: | ---: |
| total | **147** | **164** |
| source + test | **53** | **58** |
| source only | 27 | 29 |
| docs only | 30 | 34 |
| test only | 37 | 43 |

**1,016 predicate configurations were then tested exhaustively** — every one of
the 127 non-empty subsets of the seven vocabulary alternatives, crossed with two
repair-verb anchorings, two match fields (whole message, body below the subject)
and the base filter on or off. Exactly **10 configurations return 147**. Not one
of them is the predicate as stated: every one drops at least one vocabulary
alternative, and they disagree about which.

Adding the strata as a second constraint does not rescue it. Across those 10
configurations crossed with six path rules, the best fit misses by 2 cases
(53 / 27 / **31** / **36**) and gets there only by dropping `adjudicat\w+` and
`re-review` — the two terms that most directly express "adjudicated review
round", which is the predicate's whole point. No configuration reproduces all
four strata. Reaching 147 requires mutilating the predicate, and the routes to
it do not agree.

**This is the same failure the first run found in the design, now in the
replacement.** Finding 2 withdrew its own claim on the ground that a
determinate predicate reproducing the design's strata exists. The predicate is
determinate — a regex always is — but the *recorded counts* do not follow from
the *recorded predicate*, which is exactly the property that made the design's
113 unusable. A number that cannot be recomputed from its stated rule is not a
frozen population, however precisely it is written down.

### The three-case oracle gate reproduces exactly

Every published expectation held, on a harness built without reference to the
earlier implementation. The runner enforced the protocol mechanically: hard
reset and clean, detached checkout, **printed and verified `HEAD`**, refusal to
proceed on a dirty tree, and a per-path assertion that each named mirror
actually changed.

| Case | Expected | Observed | What decided it |
| --- | --- | --- | --- |
| `00df54200` | semantic kill | **semantic kill** | R passed first (23 passed). With all 3 mirrors reverted, the replay returned `1 != 0` and the guard said `review_retry_count 5 has reached max_review_retries 5` — the dispatched defect exactly. 5 of 23 tests failed. |
| `b1e7d6864` | structural kill | **structural kill** | R passed first (95 passed). The unsafe input stayed rejected: `assertEqual(r.returncode, 2)` still passed. Only the reason changed — `plan_file_outside_root != plan_file_is_symlink`. 1 of 95 failed. |
| `90cb9426e` | semantic kill on the AST repair | **semantic kill** | R passed first (9 passed). Reverting the walker made the lint report `1 skill(s) scanned, 0 finding(s)` — the fixture was scanned and the banned flags went undetected, so the pass is not a structural skip. |

Because the predicates were frozen before this run and published above, no
predicate could be written to fit a result. That is the freeze-before-observe
discipline the gate exists to test, and it held a second time.

### Both harness requirements confirmed again, by observation

**1. Reverting one mirrored copy manufactures a false survivor.** In
`00df54200` the repaired hunk is byte-identical in `.agents/skills/`,
`.claude/skills/` and `packs/core/.apm/skills/`. Reverting only `.agents` was
run as a deliberate control arm: **23 passed, exit 0.** The same suite that
reports 5 failures when all three mirrors go back reports a clean pass when one
does. A harness that reverts one copy records `survives` for a repair whose
control fires.

**2. Scored per repair, `90cb9426e` is one semantic kill and one repair with no
control at all.** The two repairs were reverted in separate arms:

| Arm | Reverted | Result |
| --- | --- | --- |
| A | AST walker only | 1 failure — the dispatched defect |
| B | ACL/SID matching only | **9 passed, exit 0** |
| C | both | 1 failure, identical to arm A |

Arm B is the decisive one, and it is stronger evidence than the first run's
byte-identical comparison. Reverting the Windows ACL repair **on its own** leaves
the suite entirely green. That repair has no control in this test, and the
reason is structural rather than incidental: the helper opens with
`if os.name != "nt": return`, so on POSIX the reverted code never runs. Scored
per commit the case reads `semantic kill` and the uncontrolled repair vanishes.

**A third unit question surfaced, and it is not yet answered.** `b1e7d6864`
answers *three* adjudicated findings, not one: the symlink rejection (P1,
source), the SKILL.md consent language (P2, prose) and a dependency record in a
new `packs/core/AGENTS.md` (P2, prose). Only the first has a source hunk this
stratum's oracle can revert. So "one outcome per adjudicated repair" does not by
itself say what to do with a repair whose oracle lives in a different stratum.
Counting it as one case understates the commit; counting all three understates
provability, because two of them were never in scope here. No outcome was
recorded for those two.

### Outcomes so far, and why they are still not a rate

Scored per repair, the four adjudicated source repairs measured to date:

| Outcome | Count |
| --- | ---: |
| semantic kill | 2 |
| structural kill | 1 |
| survives | 0 |
| unmeasurable | 1 |
| **denominator** | **4 repairs across 3 commits** |

**This is not a rate and must not be read as one.** All three commits were
hand-picked to span the outcome space, which is the opposite of a random draw.
The design's own power limit also stands: at n≈39–53 this measurement can
separate a widespread problem from a rare one and **will not support a threshold
near 10%**.

### The selection order is frozen now, before any outcome is seen

So that the draw cannot later be reordered to favour a result, the order over
the `source + test` stratum is fixed and recorded here:

- **Population:** the faithful reading of P3 described above — 164 commits, 58
  in `source + test`, on `origin/main` at `9d430418b`, committer date on or
  before 2026-09-11.
- **Order:** the 58 SHAs sorted, then shuffled with Python `random.Random(20260917)`.
- **Digest:** `sha256` of the newline-joined order is
  `10c3aaace43af05a6f1fd62078dc3923752696f3222aec6e45397c441cca5b81`.

The three gate cases land at positions **21, 44 and 50** in that order. They are
not front-loaded, which is the check that the order was not fitted to the cases
already scored.

If the owner settles on a different population, the order must be regenerated by
the same recorded procedure and its digest published before any case is run.

### What blocks the remaining 50

One decision, and it belongs to the owner because it sets the denominator of the
headline result.

**Which population is frozen?** Three options, best first:

1. **Adopt the faithful reading — 164 commits, 58 in `source + test`.** It
   recomputes from its stated rule, which is the property 147 lacks. The cost is
   that the recorded 87.5% precision was measured on a 16-case draw from the
   147, so it transfers to the 164 by assumption rather than by measurement.
2. **Recover the missing step.** Twelve commits vanish between Finding 2's 116
   and its 104, and something similar most likely separates 164 from 147. If
   that step is recoverable, 147 becomes reproducible and the precision figure
   keeps its basis.
3. **Re-derive and re-validate a fresh predicate.** Most defensible, and it
   repeats work the earlier sections already paid for.

Everything downstream is ready. The oracle discriminates, the runner enforces
the mirror and clean-tree requirements mechanically, the environment needs only
Python, pytest, git and PyYAML, and the per-case cost estimate of about 43
minutes held on all three gate cases.

### Transfer limit on this run

This run measures the instrument and the oracle, not repair provability. It
establishes that the oracle reproduces and discriminates on a second independent
implementation, and that the population is not yet reproducible. It says nothing
about how often repairs ship with a control that can fail.
