# Repair provability audit — first run: the instrumentation gate does not pass

- **Run date:** 2026-09-17
- **Owner:** eugenelim, Platform Core maintainer
- **Against:** `origin/main` at `9d430418b`
- **Verdict:** the 10-case instrumentation gate **failed on the first pass**,
  then a second round found a determinate predicate that reproduces the design's
  strata. See the erratum below, which withdraws part of Finding 2. What stands:
  the design's stated criterion does not decide the same set twice and its own
  frozen corpus contradicts its prose, so the population must be re-frozen on an
  explicit predicate before any oracle runs. The oracle phase has still not run.
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

## What has to change before this audit can run

1. **Adopt P3 as the frozen population predicate** (see the erratum): wider
   review vocabulary, commit type not `feat`, repair verb in the subject. It is
   determinate, ~95% precise, and reproduces the design's strata shares within
   4.4 points. Confirm it on a sample drawn from its own selection first. Delete
   the design's claim that the round is recorded with counts and severity bands,
   which its own corpus contradicts.
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
