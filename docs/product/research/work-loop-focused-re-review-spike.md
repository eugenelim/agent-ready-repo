# Work-loop focused re-review — validation spike

Paired broad/focused re-review measurement on identical repaired bytes, testing the riskiest
assumption of [work-loop focused re-review](../intents/work-loop-focused-re-review.md), the second
child of [work-loop delivery efficiency](../intents/work-loop-delivery-efficiency.md).

- **Run date:** 2026-09-09
- **Owner:** eugenelim, Platform Core maintainer
- **Verdict:** recorded in [Survive/kill calculation](#survivekill-calculation) below
- **Kill condition:** predeclared 2026-09-09 in the child intent, before any case ran; the exact
  clauses are quoted in the calculation section rather than restated loosely

## What this spike tests

The riskiest assumption is that a focused re-review of the accepted finding set, the repair diff,
the affected contract bytes and the demonstrated dependency consequences retains the material
defect coverage of a fresh broad re-review on the identical repaired revision, while using
materially less time and context.

Both arms inspect the same frozen repaired revision against the same frozen base with the same
reviewer role and model. Only the re-review scope differs.

## Frozen corpus

All four cases were preselected and recorded here before either arm ran on any case. No case was
replaced, split or reclassified after any result was seen.

A **repair event** is one natural repair commit answering one adjudicated review round. This
repository records that round durably in the repair commit's own message: the sustained and
refuted counts, each finding's severity band (Blocker / Concern / Nit or MAJOR / MINOR), the
adjudicated mechanism, and the remedy applied. That message is the complete adjudicated finding
set for the event, and it is what the focused envelope carries.

- **Repaired revision (R)** — the natural repair commit. Both arms review this tree.
- **Pre-repair revision (P)** — `R^`, the tree the review round ran against.
- **Base (B)** — the branch point, computed as `git merge-base M^1 M^2` for the merge commit `M`
  that landed the branch on `main`. Every case has **zero merge commits in `B..R`**, so no merge,
  rebase or base change invalidates focus in this corpus.
- **Whole change** — `B..R`, the subject the broad arm re-reviews.
- **Repair diff** — `P..R`, the subject the focused envelope carries.

| Case | Stratum | Repaired revision (R) | Pre-repair (P) | Base (B) | Whole change | Repair diff |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | low-risk | `ab6016abe` | `fcbd33f38` | `02742751a` | 24 files, +2176/−178 | 3 files, +31/−24 |
| F2 | ordinary | `27693afb5` | `9b95946c1` | `a06fb2e6c` | 14 files, +745/−332 | 9 files, +191/−47 |
| F3 | ordinary | `af84562eb` | `c056eea72` | `1134701ba` | 26 files, +1188/−92 | 2 files, +126/−29 |
| F4 | high-risk | `1423734b6` | `71b8cdee5` | `59bfaf892` | 13 files, +856/−14 | 8 files, +203/−38 |

Subject digests, so a later edit cannot silently change what was reviewed. Each is the SHA-256 of
the diff text, first 16 hex characters.

| Case | Whole-change digest | Repair-diff digest | Accepted contract | Contract digest at R | Contract changed by the repair |
| --- | --- | --- | --- | --- | --- |
| F1 | `c5defd3414abfb18` | `58f83c2ac22eaba5` | `docs/product/briefs/agent-authoring-input-quality.md` | `0f8c4e68322ba5ed` | yes |
| F2 | `668d57c6f7b63a91` | `731d239e2c1f1d73` | `docs/specs/guide-callout-inventory/spec.md` | `6f04861765160f53` | yes |
| F3 | `d2f6cc911879f984` | `77db3b221a40abec` | `docs/specs/verification-ledger/spec.md` | `f9e29fea21b91d5b` | no |
| F4 | `1347edce3491511f` | `0485eb28dbffd43b` | `docs/adr/0102-path-scoped-semgrep-exclusion-for-scanner-performance.md` | `be69cd51b5816b46` | yes |

### Why each case sits in its stratum

The stratum rule was fixed before selection. **Low-risk**: the repair touches only prose or test
files and no protected consequence class is reachable from it. **Ordinary**: the repair changes
user-visible behaviour, agent-facing instructions or a released pack surface, with one owner and no
destructive, migration, security-boundary or breaking-public-contract trigger. **High-risk**: the
repair reaches a protected class — security, privacy, data loss, destructive operation,
migration or mixed version, public contract, or human approval.

**F1 — low-risk.** `fix(docs): close the five sustained round-11 findings`. Three files, all prose:
one delivery brief and two research documents. Adjudicated 5 sustained, 3 refuted, 0 indeterminate,
with two Blockers, one Concern and two Nits. The Blockers are a pinned branch-local commit that had
orphaned for the third time, and an exact review-round count that decayed. No executable behaviour
changes, so no protected class is reachable from the repair.

**F2 — ordinary.** `fix(guides): close nine adjudicated review findings`. Nine files spanning two
guide-lint tools, a web rendered-output test, two spec bodies, two plan bodies and the spec
register row. The headline defect is that the falsifiability harness contained the defect it exists
to catch: three ledger rules had no distinguishing killing mutation. It changes executable guard
behaviour and a register row, but no protected class: a false-green lint is a quality consequence
here, not a security or data-loss one.

**F3 — ordinary.** `fix(tests): close the four holes the guard re-review found`. Two files: a
roster contract test and the shipped `CONVENTIONS.md` convention seed. Verdict entering the repair
was `GUARD STILL HOLLOW`. Four adjudicated holes, each reproduced before being fixed: closed-set
membership that deleted its own assertions, routing checks that accepted any plausible phrasing, a
status guard that proved a string was present rather than that the guard admitted the status, and a
changelog-adjacency check that took the first `[core]` heading anywhere in the file. It edits a
released convention seed, so it is beyond low-risk, but no protected class is reachable.

**F4 — high-risk.** `fix(sast): apply final-review findings on the semgrep gate`. Eight files: the
`Makefile` gate recipe, two SAST tools, a self-test, an ADR pair and the `workspace.toml` residual
row. The protected class is security: the change is to a guarding control, and its adjudicated
defects include a version preflight that reported an unparseable version as "below the floor" — the
commit records this in terms of how a security gate gets bypassed — a residual statement that
contradicted the branch's own reverted CodeQL threat-model setting, and a wrapper that dropped the
offending token from every `--strict` diagnostic. It also carries a registered-residual link that
the ADR renumber left pointing at an unrelated ADR.

## Pinned configuration

| Pinned item | Value |
| --- | --- |
| Host | Claude Code 2.1.267, macOS (Darwin 25.5.0) |
| Controller model | `claude-opus-5` |
| Reviewer role | `adversarial-reviewer`, both arms, every case |
| Reviewer model | `opus`, from `.claude/agents/adversarial-reviewer.md` frontmatter, unmodified |
| Reviewer tools | `Read, Grep, Glob, Bash`, agent-definition default, unmodified |
| Adjudicator role | `finding-adjudicator`, model `opus`, tools `Read, Grep`, unmodified |
| Reviewer-role revision | `packs/core/.apm/agents/` at working-tree revision `d44484b29` |
| Policy revision | `packs/core/.apm/skills/work-loop/` at working-tree revision `d44484b29` |
| Contract revision | per case, digest-pinned above |
| Repository under review | one disposable git worktree per arm per case, checked out at R |

Each arm gets its **own** worktree even though neither is supposed to write, because a reviewer
holding `Bash` can mutate the tree and a shared checkout would let one arm's side effect reach the
other.

## Arm definitions

**Baseline** is the currently installed policy, read from
`packs/core/.apm/skills/work-loop/SKILL.md:727`: *"Full mode: after any applied sustained REVIEW
finding, re-run the reviewer or reviewer set that produced it."* The reviewer is re-run over the
whole change `B..R` with no narrowing. Its preparation is one `git diff B R`.

**Candidate** is the focused re-review the intent proposes. The reviewer receives an envelope
containing the complete adjudicated finding set and remedies for the repair event, the repair diff
`P..R`, the affected contract bytes, and the dependency consequences demonstrated for that repair.
The envelope states explicitly that it is a subject boundary and not a suppression instruction: the
reviewer may follow evidence outside it and must report any material defect it observes, including
a protected-class consequence.

Candidate preparation is **dispatched, not hand-written**, so its cost is provider-measured rather
than absorbed into the controller. One envelope-preparation call per case precedes the focused
reviewer call, and both are counted in the candidate arm's tokens and elapsed time.

Specialist routing, adjudication, repository gates and owner authority are unchanged in both arms
and are outside this comparison, exactly as the intent's Boundary requires.

**Arm order alternates across cases.** F1 and F3 run baseline first; F2 and F4 run candidate first.
Each arm runs in a separate clean agent context with no access to the other arm's findings.

## Telemetry mechanism

Unchanged from the [review-economics spike](work-loop-review-economics-spike.md#telemetry-mechanism-and-precision),
whose instrument is reused: token counts are the inference provider's own `usage` blocks summed
across every API request in a call, read from the call's own JSONL transcript. Elapsed time is the
span between the transcript's first and last record. Long inter-record gaps are split into human
permission waits (a gap between a tool request and its result) and model or queue stalls
(everything else), so contamination of the wall-clock figure is visible rather than buried.

## The run stopped after one case

The intent's Activity clause reads: *"Stop immediately on a protected-class, Blocker, or High miss;
otherwise run all four cases."* That stop rule fired on **F1**, the first case run. F2, F3 and F4
were preselected and frozen but **never run**, and no arm of them was executed or measured. The
corpus above is recorded unchanged so the stop is legible: the cases were chosen before the result,
not narrowed to it.

## Raw per-call measurements

Every row is one dispatched agent call. Token columns are the inference provider's own counts
summed across that call's API requests. The `blind` row is the independent union adjudication and
belongs to neither arm.

| Case | Arm | Phase | API reqs | Total tokens | Elapsed s | Permission s | Stall s | Active s |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| F1 | baseline | broad re-review | 110 | 10,603,322 | 529.9 | 0.0 | 0.0 | 529.9 |
| F1 | candidate | envelope preparation | 24 | 1,105,974 | 241.0 | 0.0 | 117.6 | 123.4 |
| F1 | candidate | focused re-review | 22 | 908,816 | 178.0 | 0.0 | 0.0 | 178.0 |
| F1 | blind | union adjudication | 33 | 2,094,066 | 282.0 | 0.0 | 167.7 | 114.3 |

Run total: 4 measured agent calls, 14,712,178 provider-reported tokens, 1,230.9 s (20.5 min)
elapsed, decomposing into 945.6 s active work, 285.3 s model or queue stall, and 0 s waiting on a
human permission grant.

### Cost comparison on F1

| Arm | Calls | Tokens | Elapsed s | Stall s | Stall share | Active s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline (broad re-review) | 1 | 10,603,322 | 529.9 | 0.0 | 0.0% | 529.9 |
| Candidate (preparation + focused re-review) | 2 | 2,014,790 | 418.9 | 117.6 | 28.1% | 301.3 |
| **Saving** | | **81.00%** | **20.95%** | | | **43.14%** |

The candidate's cost includes envelope preparation, which was dispatched rather than hand-written
precisely so that it could not disappear from the candidate's bill. Preparation is 54.9% of the
candidate's tokens and 57.5% of its elapsed time; the focused reviewer call alone is 908,816
tokens against the broad reviewer's 10,603,322.

**The elapsed-time reading on F1 is contaminated and is not usable.** The candidate arm recorded
117.6 s of model or queue stall, 28.1% of its elapsed time, against the intent's admissibility bar
of 10%. Only one agent ran at a time throughout, so this is host or provider load rather than
self-inflicted concurrency. Under the intent's rule this case would be the one permitted re-run on
a quiet host — but the verdict below does not rest on the elapsed clause, and re-running it could
not change the verdict, so it was not re-run. Tokens and permission wait are unaffected: permission
wait was 0 s in both arms.

## Blinded union and defect clusters

The two arms produced 15 findings in total — 9 from the broad arm, 6 from the focused arm. They
were assembled into one union file with reviewer identity, review policy, review scope, pass number
and arm-specific worktree paths removed, identifiers renumbered `F1-U-01` … `F1-U-15`, and ordering
made origin-independent by hashing the original identifier. A mechanical scan for residual identity
tokens returned two hits, both verified false positives: the word "policy" inside the union file's
own preamble, and the real filename `policy-arrival-validator.md`. Zero identity leaks reached the
adjudicator.

A fresh `finding-adjudicator` — on its own pristine worktree at the frozen revision, having run
neither arm — adjudicated the union, ruled severity and protected class on its own judgement rather
than accepting what a finding asserted, and grouped the findings into defect clusters. The private
key mapping blinded identifiers back to arms was not available to it and was applied only
afterwards.

The adjudicator's own severity rulings moved findings in both directions: it ruled the duplicated
release entry down from Blocker to High, ruled the ablation self-contradiction down from Blocker to
Medium because the artifact ships to no adopter surface, and ruled one finding reported as a Concern
up to Medium. It refuted one finding and returned two as indeterminate.

| Cluster | Severity | Protected class | Reached by |
| --- | --- | --- | --- |
| `CH-CONFLICT` | Blocker | public-contract | broad only |
| `NOW-STALE` | Blocker | public-contract | broad only |
| `CH-DUP-2250` | High | public-contract | broad only |
| `ABL-DELTA` | Medium | none | both |
| `FIG-MULTIPLE` | Concern | none | both |
| `BACKLOG-MISSING` | Concern | none | broad only |
| `CITE-LINES` | Nit | none | broad only |
| `ABL-RANGE` | Concern | none | focused only |
| `ROUND-POINTER` | Concern | none | focused only |
| `BRIEF-SIZE` | Concern | none | not sustained (indeterminate) |
| `ROUND-BULLET` | Concern | none | not sustained (indeterminate) |
| `ROUND-THIRD` | Nit | none | not sustained (refuted) |

Nine sustained clusters. Two were reached by both arms, five by the broad arm alone, two by the
focused arm alone.

### The three protected-class clusters the focused arm missed

All three are public-contract consequences in `docs/product/changelog.md` and the projection derived
from it, and all three share one root cause: **an unresolved merge conflict was committed into the
released region of the changelog** by `487b48891`, an ordinary implementation commit earlier on the
branch. The markers are present at both the pre-repair revision `fcbd33f38` and the repaired
revision `ab6016abe`, and absent at the base `02742751a`. This was verified against the git objects
directly, not the checkout, before any of it was treated as data:

```
git show ab6016abe:docs/product/changelog.md | grep -nE '^(<<<<<<<|=======|>>>>>>>)'   # 6 lines
git show 02742751a:docs/product/changelog.md | grep -cE '^(<<<<<<<|=======|>>>>>>>)'   # 0
git log --oneline -S'<<<<<<< HEAD' --pickaxe-regex 02742751a..ab6016abe -- docs/product/changelog.md
```

**1. `CH-CONFLICT` — Blocker, public contract.** Six literal conflict-marker lines sit between the
`[Unreleased]` header and the `[core][2.25.3]` entry, and the `[core][2.25.4] — 2026-09-08` heading
no longer exists anywhere in the file. Its Highlights and `### Fixed` bullets now sit on the HEAD
side of the `[core][2.25.7]` block, while the branch's actual rubric outcome sits after the
`=======`. The adjudicator confirmed independently that 2.25.4 was a real shipped release, because
the committed `/now/` projection still carries its group. A released entry is destroyed and the
current release advertises another release's change.

**2. `NOW-STALE` — Blocker, public contract.** `web/src/lib/now-highlights.generated.json` no longer
matches the changelog it is derived from, so the staleness assertion in
`tools/test_build_site_routing.py` fails, and `Makefile:584` runs that suite inside `make test`. On
regeneration the branch's own user-visible outcome still would not reach the public page, because
the rubric bullet falls after `### Fixed` rather than inside Highlights. The adjudicator established
this statically rather than by running the suite, and ruled it a separate defect from the conflict
itself: repairing the changelog leaves the committed projection stale until it is regenerated.

**3. `CH-DUP-2250` — High, public contract.** The `[core][2.25.0] — 2026-09-04` entry appears twice
verbatim, at lines 258 and 276, both outside every conflict region. The adjudicator ruled it a
distinct cluster on exactly that ground — it survives any repair of the conflict — and ruled it down
from the reported Blocker because no content is destroyed.

None of the three lies inside the repair diff, and none is a consequence of the repair. They are
pre-existing defects elsewhere in the change that a whole-change re-review resamples and a focused
re-review, by construction, does not.

### What the focused arm did find

The focused arm was not merely a subset. It reached two sustained clusters the broad arm missed —
`ABL-RANGE`, where removing a branch-local pin left the load-bearing byte-identity claim with no
antecedent for "the measured range" anywhere in the file, and `ROUND-POINTER`, where the substitute
for a removed count points readers at artifacts under `.context/reviews/` that `.gitignore`
excludes, so the pointer resolves to nothing for any reader of the repository.

It also produced the single most incisive finding in the corpus, on `ABL-DELTA`: the repair closed
the *mechanism* of the finding it answered — no orphaned commit is pinned any more — while
re-instantiating that finding's *root cause* in a new form, leaving the file denying it keeps a
delta list and then keeping one three lines later. The broad arm reached the same cluster but framed
it as a documentation-consistency Concern; the focused arm identified the repair-induced structure.
That is direct support for the intent's second assumption even as its first assumption fails.

## Survive/kill calculation

### Verdict: Killed

The kill condition, quoted from the child intent exactly as predeclared on 2026-09-09 before any
case ran:

> Kill or reshape if the focused arm misses any independently adjudicated sustained protected-class,
> Blocker, or High-severity cluster found by the broad arm; misses more than one other independently
> adjudicated sustained Medium or Concern cluster across the corpus; fails to reduce median
> provider-reported re-review tokens by at least 30% across the three non-high-risk cases; or fails
> to reduce median uncontaminated re-review elapsed time by at least 20% across those cases.

**Clause 1 — any missed protected-class, Blocker or High cluster. FIRES.** The clause requires
*any* such miss. There are three, all on the first case: `CH-CONFLICT` (Blocker, public contract),
`NOW-STALE` (Blocker, public contract) and `CH-DUP-2250` (High, public contract). Each was sustained
by an independent adjudicator blind to arm identity, each was assigned its severity and protected
class by that adjudicator rather than by the reporting reviewer, and each traces to the broad arm
alone through a cluster containing no focused-arm finding. This clause is not marginal, and it is
the whole verdict.

**Clause 2 — more than one *other* sustained Medium or Concern miss. Does not fire on the evidence
taken.** The focused arm's remaining misses on F1 are `BACKLOG-MISSING` (Concern) and `CITE-LINES`
(Nit); the Nit is not in the clause's class, so the count of other Medium-or-Concern misses is one,
which is not more than one. This is a one-case count and the clause was written to run across four
cases, so it is reported as not fired *on the evidence taken* rather than as passed.

**Clauses 3 and 4 — the token and elapsed-time bars. Unmeasured.** Both compute a median across the
three non-high-risk cases. Only one non-high-risk case ran, so no median exists and neither clause
is decidable. What was measured on F1 is an 81.00% token saving and a 20.95% elapsed saving — both
comfortably past their bars — and it is stated here precisely so that it is on the record that
**the cost case was not the problem**. It cannot be used to offset clause 1, and F1's elapsed figure
is in any case contaminated at 28.1% stall.

### What this kills, and what it does not

The killed proposition is the specific bet the intent named: that focused post-repair re-review
retains the material defect coverage of a broad re-review on identical repaired bytes. On the one
case run it did not, and the miss was in the most protected class the corpus contains.

Three things survive the kill, because they were measured rather than assumed:

- **The cost mechanism works, and works better than the prior spike suggested.** Narrowing the
  re-review subject cut tokens by 81.00% on this case even after dispatched envelope preparation is
  charged to the candidate. The predecessor spike measured a 35.8% review-phase saving; isolating
  the mechanism raised it. Cost was never the reason to reject this policy.
- **The focused reviewer is genuinely better at the repair itself.** It reached two sustained
  clusters the broad arm missed and was the only arm to identify that the repair re-instantiated the
  root cause of the finding it was closing. The intent's second assumption — that a focused reviewer
  detects repair-induced and reopened defects reliably — held on this case.
- **The failure is structural, not incidental.** The three missed clusters are not subtle. They are
  committed conflict markers and a destroyed release entry in the published changelog. A focused
  re-review missed them for the only reason it could: they are nowhere near the repair. No amount of
  envelope quality reaches a defect that a different commit introduced in a different file.

### The one honest complication, which does not change the verdict

Under the shipped policy the *initial* broad review runs before any repair, and these three defects
existed at the pre-repair revision, so an initial broad review had the opportunity to catch them.
The intent explicitly preserves that initial pass. A reader could therefore argue that this corpus
punishes focused re-review for a failure the full policy would have absorbed upstream.

That argument is recorded and rejected, for two reasons. First, the kill condition is predeclared
and one-directional by design: it asks whether the focused arm misses what a broad re-review of the
identical repaired revision finds, and it does. Weakening it after seeing the result is precisely
what the predeclaration exists to prevent. Second, the argument is empirically weak here: this
repository's own history shows the initial pass did *not* catch them — the markers survived from
`487b48891` through round 11 of an eleven-round review and were still committed at the tip. A
guardrail whose safety depends on an earlier pass that demonstrably missed the defect is not a
guardrail. If the policy is reshaped, this is the gap the reshape has to close.

### Limitations

Each states which direction it pushes the result.

**One case, not four.** The stop rule is what the intent asked for, but it means the corpus behind
the verdict is a single low-risk case. Clause 1 needs only one miss and fires decisively; clauses 3
and 4 need medians and are unmeasured. Direction: makes the cost evidence weak and the safety
evidence narrow, but does not weaken clause 1, which is satisfied by any single miss.

**F1 is a low-risk case that turned out to carry high-risk defects.** It was stratified low-risk on
its *repair* — three prose files — which is what the stratum rule keys on, and that classification
was recorded before the run. The whole change around it carried public-contract Blockers introduced
upstream. Direction: this is adverse to the candidate, and a fair reading should note that a corpus
without a committed merge conflict might not have fired clause 1 on case 1. It is also exactly the
kind of state the guardrail exists to catch, and it was not selected for.

**Elapsed time is contaminated on the candidate arm.** 28.1% stall against a 10% bar, with only one
agent running. Direction: neutral on the verdict, which does not use the elapsed clause; it means
clause 4 would have been unmeasured even had four cases run without a re-run on a quiet host.

**The adjudicated finding set is reconstructed from the repair commit's message.** This repository
records the round durably there — sustained and refuted counts, severity bands, adjudicated
mechanism and remedy — but it is the author's record of the round, not the reviewer's original
report, which did not survive. Direction: if anything it flatters the candidate, whose envelope is
built from that record; a noisier real finding set would make focus harder, not easier.

**The broad arm was run once, not iterated to Clean.** The shipped policy iterates. Direction:
understates baseline cost, so it cannot manufacture a candidate cost win.

### Evidence retention

Owner decision, 2026-09-10: retain this findings report only. The frozen corpus, arm reports,
focused envelope, blinded union, adjudication record, measurements, blinding key and helper scripts
were deliberately not retained in the repository. The report preserves the result and method, but
the calculation cannot be rerun from repository artifacts alone.
