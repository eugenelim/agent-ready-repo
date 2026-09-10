# Work-loop focused re-review

- **Status:** Draft
- **Kind:** outcome
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** work-loop-delivery-efficiency — [Work-loop delivery efficiency](work-loop-delivery-efficiency.md)

## Outcome

- **Steerable input:** Replace whole-change broad review after a bounded repair with review of the complete accepted finding set for that repair event, its repair diff, affected contract bytes, and demonstrated dependency consequences, while leaving the initial broad review and triggered specialist coverage unchanged.
- **Lagging outcome:** Repaired changes reach a defensible review stopping point with materially lower reviewer wall-clock time and model-token cost because unchanged context is not resampled after every repair.
- **Guardrail:** Focused re-review misses no independently adjudicated protected-class, Blocker, or High-severity defect found by a broad re-review of the identical repaired revision. Initial broad review, specialist routing, adjudication, repository gates, and owner authority do not weaken.

## Opportunity

- **Functional job:** Verify that an accepted finding was closed, and that its repair did not introduce or reopen a material defect, without paying to review the entire unchanged change again.
- **Emotional job:** Feel that another review pass is purchasing evidence about the repair rather than reopening an unbounded search.
- **Social job:** Give maintainers a stopping decision whose assurance and economic basis can be explained from the reviewed bytes.
- **Struggling moment:** After an implementer repairs a sustained finding, the current loop sends the whole change through another fresh broad review. The six-case economics spike observed the same number of reviewer calls under both policies, but narrowing the later calls reduced review tokens by 35.8% and caught repair defects in C1, C3, and C6; the experiment did not isolate the focused mechanism from its unsafe consequence-bound-blocking companion.

## Boundary

- Includes only post-repair re-review scope, context preparation and supply, affected-byte and dependency invalidation, re-review wall-clock and token measurement, and comparative defect coverage on the identical repaired revision.
- One repair event is one natural repair revision responding to one adjudicated review round. Every sustained finding answered by that revision stays in the case; findings may not be split or selected after results are visible.
- The focused reviewer receives the complete sustained finding set and adjudicated remedies, the repair diff, governing contract, changed contract bytes, and dependencies plausibly affected by that repair. It may inspect beyond the supplied envelope when evidence indicates an omitted consequence, and it may report any material defect it observes, including a protected-class consequence; focus is a subject boundary, not a suppression instruction.
- Both the repaired revision and its base are frozen and verified. A base change, merge, rebase, changed contract byte, or repair outside the accepted finding set invalidates focus and routes the case to broad review rather than treating an incomplete interdiff as evidence.
- The broad comparison arm receives the repository's current ordinary re-review context. Both arms use the same frozen repaired revision, reviewer role and model configuration; only re-review scope differs.
- Excludes consequence-bound blocking, altered severity semantics, initial broad-review removal, specialist-review removal, adjudication removal, repair-authoring improvements, convention delivery to implementers, gate scheduling, orchestration, and revision-bound reuse across separate changes.
- The validation probe may use frozen disposable worktrees and does not change shipped review policy.

## Owner

- eugenelim, Platform Core maintainer.

## Assumptions

- A repair's material consequence surface can be bounded from its accepted finding, changed bytes, governing contract, and demonstrated dependencies without silently excluding an affected protected class.
- A focused reviewer can detect repair-induced and reopened defects on that surface as reliably as a broad reviewer inspecting the identical repaired revision.
- Narrower context reduces tokens and wall-clock time even when the number of reviewer calls does not fall.
- The prior spike is directional evidence, not an isolated comparison: seven focused re-review calls caught three repair-induced defects, while review tokens across all six cases fell from 84.7M to 54.3M; its three protected misses arose in the combined candidate and cannot be attributed to this mechanism alone.
- External evidence makes the interaction credible but does not settle this policy: patch-set comparison is established practice, smaller review subjects can reduce false positives without reducing review time, and base drift can make an interdiff incomplete. The [agentic loop effectiveness survey](../research/agentic-loop-effectiveness-survey.md#1-focused-re-review-is-plausible-not-yet-proven-safe) owns that evidence and its limits.

## De-risking

- **Door:** Two-way. The policy can be evaluated on frozen repaired revisions and discarded without changing shipped review behavior.
- **Approach:** `validate-first`, overriding the two-way-door default because the probe changes an assurance boundary and must establish comparative coverage before delivery.
- **What would have to be true:** The two arms must inspect identical repaired bytes against the same verified base; the focused envelope must cover the complete repair-event finding set, every changed contract, and every plausible dependency consequence; independent adjudication must distinguish the same defect expressed differently; the focused arm must retain material coverage and produce meaningful token and elapsed-time savings after preparation cost is included.
- **Riskiest assumption:** A focused re-review of the accepted finding, repair diff, affected contract bytes, and demonstrated dependencies retains the material defect coverage of a fresh broad re-review on the identical repaired revision while using materially less time and context.
- **Kill condition (predeclared 2026-09-09):** Kill or reshape if the focused arm misses any independently adjudicated sustained protected-class, Blocker, or High-severity cluster found by the broad arm; misses more than one other independently adjudicated sustained Medium or Concern cluster across the corpus; fails to reduce median provider-reported re-review tokens by at least 30% across the three non-high-risk cases; or fails to reduce median uncontaminated re-review elapsed time by at least 20% across those cases.
- **Measurement accounting:** The deciding token and elapsed intervals begin when either arm starts constructing its re-review context and end at its re-review verdict. Record preparation and reviewer execution separately so envelope work cannot disappear from the candidate cost. Also report total critical-path elapsed time with permission wait and model or queue stall split out; this operational clock does not replace the predeclared uncontaminated threshold.
- **Measurement admissibility:** An elapsed-time case is uncontaminated only when both arms record no human permission wait and model or queue stall is no more than 10% of elapsed time. Re-run one contaminated case once on a quiet host before verdict; if it remains contaminated, the wall-clock clause is unmeasured and the intent cannot survive, though safety, tokens, and total critical-path time are still reported.
- **Corpus:** Preselect four natural repair events before either comparison arm runs: one low-risk, two ordinary, and one high-risk. Each must preserve the complete pre-repair finding set and adjudication for one review round, the identical frozen post-repair revision and base, accepted contract, repair diff, and usable timing and provider-token telemetry. Do not split a repair event or replace a case after seeing either arm's result.
- **Activity:** For each frozen repair event, run one current-policy broad re-review and one focused re-review with arm order alternated. Blind policy identity, independently adjudicate and cluster the union, compare misses by severity and protected class, and report context-preparation and reviewer tokens, admissible elapsed time, and total critical-path time. Stop immediately on a protected-class, Blocker, or High miss; otherwise run all four cases.
- **Status:** Run 2026-09-09; killed on the protected-class clause after one case, under the
  Activity clause's own immediate-stop rule. Evidence in
  [the spike record](../research/work-loop-focused-re-review-spike.md).

## Method amendments (2026-09-09, before execution)

These four decisions were made and recorded **before any arm ran**. None was made or changed after a
result was visible, and none touches the kill condition, the thresholds or the corpus size.

1. **The adjudicated finding set is read from the repair commit's own message.** The original
   reviewer reports for historical repairs did not survive; this repository instead records each
   round durably in the repair commit — sustained and refuted counts, per-finding severity band, the
   adjudicated mechanism and the remedy applied. That record is what makes a natural repair event
   recoverable at all, and it is the finding set the focused envelope carries.
2. **A whole-change size bound was applied at selection.** Candidates were restricted to a change of
   at most 30 files and roughly 2,600 changed lines, so the broad arm could genuinely review its
   whole subject rather than degenerate. This excludes the largest changes, which are where focus
   would plausibly save the most, so it is conservative against the candidate.
3. **Candidate envelope preparation is dispatched, not hand-written.** Preparation runs as its own
   measured agent call, so its tokens and elapsed time are provider-reported and cannot disappear
   into the controller's context.
4. **Calls run strictly one at a time.** The predecessor spike's wall-clock clause was destroyed by
   self-inflicted concurrency; sequential execution is the only way the predeclared elapsed-time
   threshold could be measured at all.

## Validation result (2026-09-09)

**Verdict: killed.** The deciding clause is the first: *"misses any independently adjudicated
sustained protected-class, Blocker, or High-severity cluster found by the broad arm."* On F1, the
first case run, the focused arm missed three — two Blockers and one High, all public-contract, all
in `docs/product/changelog.md` and the projection derived from it. Each was sustained by an
independent adjudicator blind to arm identity, which assigned severity and protected class on its
own judgement. The Activity clause's immediate-stop rule then halted the run; F2, F3 and F4 were
frozen and preselected but never executed.

The three misses share one root cause: an unresolved merge conflict committed into the released
region of the changelog by an ordinary implementation commit earlier on the branch, present at both
the pre-repair and repaired revisions and absent at the base. None of it lies inside the repair
diff.

**Assumptions falsified.** The riskiest assumption fails: a focused re-review did not retain the
material defect coverage of a broad re-review on identical repaired bytes. With it fails the first
assumption, that a repair's material consequence surface can be bounded from its finding, changed
bytes, contract and demonstrated dependencies without silently excluding an affected protected
class — the excluded class here is public contract, and the exclusion is structural rather than a
quality failure of the envelope.

**Assumptions that survived.** The second assumption held: the focused reviewer detected
repair-induced and reopened defects reliably, reached two sustained clusters the broad arm missed,
and was the only arm to identify that the repair closed its finding's mechanism while
re-instantiating that finding's root cause in a new form. The third assumption held decisively:
narrower context cut tokens by 81.00% on this case even after dispatched envelope preparation is
charged to the candidate, against a 30% bar. **Cost was never the reason to reject this policy.**

**Clauses not decided.** The token and elapsed-time clauses both compute a median across three
non-high-risk cases; one ran, so no median exists and both are unmeasured. F1's elapsed reading is
separately contaminated at 28.1% model or queue stall against the 10% admissibility bar, with only
one agent running at a time, so it is host load rather than experiment design.

**Limitations.** One case, not four. F1 was stratified low-risk on its repair — three prose files —
and that classification was recorded before the run; the whole change around it turned out to carry
public-contract Blockers introduced upstream, which a corpus without a committed merge conflict
might not have contained. The broad arm was run once rather than iterated to Clean, which
understates baseline cost and so cannot manufacture a candidate win. The spike record holds the
full list with the direction each pushes.

**The complication that does not change the verdict.** The shipped policy runs an initial broad
review before any repair, and these defects existed at the pre-repair revision, so a reader could
argue the full policy would have absorbed them upstream. Recorded and rejected: the kill condition
is predeclared and one-directional on the identical repaired revision, and this branch's own history
shows the initial pass did not catch them — the markers survived eleven review rounds and were still
committed at the tip. If this intent is reshaped, that is the gap the reshape must close.

```yaml
validation_hook:
  assumption: Focused post-repair re-review retains the material coverage of broad re-review on identical repaired bytes while using materially less time and context.
  kill_condition: Kill or reshape on any protected-class, Blocker, or High miss; more than one other Medium or Concern miss; less than 30% median token saving; or less than 20% median uncontaminated elapsed-time saving across the three non-high-risk cases.
  activity: Preselect four natural repair events without splitting their adjudicated finding sets, freeze each repaired revision and base, run broad and focused re-review under pinned configuration, independently adjudicate the blinded union, and compare coverage plus preparation and execution cost.
  status: run 2026-09-09; killed on the protected-class clause after the first case, under the Activity clause's immediate-stop rule. Three sustained public-contract clusters (two Blocker, one High) were reached by the broad arm alone. The token and elapsed-time clauses need medians over three non-high-risk cases and are unmeasured; the one case measured an 81.00% token saving against a 30% bar, so cost is not the basis of the verdict. Evidence in docs/product/research/work-loop-focused-re-review-spike.md
```

## Projection

- The hook was killed, so no delivery brief is projected from this intent as shaped. The
  protected-class clause decided it. The cost clauses are unmeasured and the one measured case
  cleared its token bar by a wide margin, so cost is recorded and is not an independent basis for
  the verdict. The [spike record](../research/work-loop-focused-re-review-spike.md#survivekill-calculation)
  holds the calculation.
- What a reshape would have to solve, stated from the measured failure rather than from the
  proposal: a focused re-review cannot see a defect that a different commit introduced in a
  different file, and the initial broad review is not a reliable backstop for it — on this branch
  that pass missed committed conflict markers through eleven rounds. A reshape needs a mechanism
  that keeps whole-change coverage of protected surfaces while narrowing the semantic re-review, and
  a deterministic check for committed conflict markers and changelog or projection integrity is the
  obvious candidate, since all three misses are mechanically detectable and none needed a reviewer.
  The parent's later corpus check found only one self-corrected conflict-marker incident in 5,001
  commits and therefore rejects a dedicated conflict-marker gate; any future reshape must use a
  generic mechanical-residue sweep rather than promote this one incident into its own control.
- Repair correctness remains an independent sibling. Its result does not depend on this one, and
  this kill does not gate it.

## Source

- Mode: repo-origin
- Locator: docs/product/intents/work-loop-delivery-efficiency.md
- Revision: sha256-bytes-v1:8ef6dc9292a5d16304f68a392ab590abd56d3572883076aae47008741d1f37cf
- Authority: repo-origin
