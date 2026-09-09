# Paired ablation: does the spec-authoring rubric change what an author produces?

> Discipline: applied (measured in-agent, pre-registered challenge set)

Run 2026-09-04 against
[`spec-authoring-rubric.md`](../../../packs/core/.apm/skills/new-spec/references/spec-authoring-rubric.md)
as it stood that day. The result **does not** settle whether a skill reference
is the right delivery mechanism — see § "What this does not measure".

**The shipped rubric has moved since, and the move misses every scored
paragraph.** No revision is pinned here: every candidate was a branch-local
commit, which orphaned on the next rebase and would not survive a squash merge —
the decay this document exists to avoid. What the claim rests on instead is the
list of scored paragraphs below, each of which was byte-identical across the
measured range at the time of the run: D1 and D2's derivation and
hand-enumeration clauses, D3's positive-path paragraph, D4's projection
paragraph, D5's empty-state tell, and D6's non-waivable-control bullet. That is
a scored-region list, not a delta list; a delta list was kept once and decayed
within two rounds, so none is kept.

Later edits fell on class 3's and class 6's *Move* paragraphs, class 6's
*Draft narration* bullet, and the optional-syntax section — none of them scored.
So the scores below stand, and § "Reproducing it" rebuilds arm B from the
*current* file, which differs from the measured one in those unscored places.

## Design

A randomised paired ablation over a challenge set, which is the design this
repository's [oracle survey](agent-behavior-oracle-patterns-survey.md) names as
the valid one for "did this rule bind?". Both arms received an identical,
self-contained brief: the shipped `assets/spec.md` § Acceptance Criteria
guidance, four draft criteria, a deferral, and one restated rule. The treatment
arm's brief additionally carried the rubric. Nothing else differed.

- **Arm A (control)** — shipped criterion-shape guidance only. The pointer this
  change added to `assets/spec.md` was stripped, so the arm had no route to the
  rubric. Verified by asserting the string `spec-authoring-rubric` was absent
  from the brief before dispatch.
- **Arm B (treatment)** — the same brief plus the rubric.

Two runs per arm, one fresh agent per run, so repeated runs are independent
samples rather than one sample and two recollections. Each agent was given the
brief path and instructed to read nothing else, run no command, and search no
repository; each made exactly one tool call, so no arm reached the repository.

Word counts: arm A 1,281, arm B 3,111. The arms are therefore **not** matched on
brief length, which § "Confounds" addresses.

## The six pre-registered defects

Each was chosen because it is **not named** by the guidance arm A receives and
**is** named by the rubric. Arm A named four of the six anyway. That falsifies
the *selection* for those four — they do not isolate a marginal contribution,
because both arms had a route to them — and it is why § "Why the four made no
difference" reports them as a null result about reachability rather than as
evidence for the rubric. D3 and D4, where arm A had no route, are the only rows
the selection holds for, and the only rows the headline claim rests on.

| # | Seeded defect | Rubric class |
| --- | --- | --- |
| D1 | A hand-copied permission set whose registry is the machine-readable source | 4, derivable enumeration |
| D2 | An exact count ("14 permissions") over a set that grows | 4, decays |
| D3 | Three refusals with no valid input that must be accepted | 3, one-sided contract |
| D4 | A criterion pinned to `build/audit-report.json`, a generated path | 4, targets a projection |
| D5 | "No manifest produces an unhandled exception" — true on an empty set | 2, cannot fail |
| D6 | A `Never do` deferral dropping path-traversal validation | 6, cuts a non-waivable control |

**Positive control.** One draft criterion also conjoined three predicates, which
the shipped shape rules already own. All four runs split it, so all four are
valid samples and arm A's guidance demonstrably reached the agent.

## Result

| Defect | A run 1 | A run 2 | B run 1 | B run 2 |
| --- | :--: | :--: | :--: | :--: |
| D1 derivable enumeration | ✓ | ✓ | ✓ | ✓ |
| D2 decays | ✓ | ✓ | ✓ | ✓ |
| D3 one-sided contract | ✗ | ✗ | ✓ | ✓ |
| D4 targets a projection | ✗ | ✗ | ✓ | ✓ |
| D5 cannot fail | ✓ | ✓ | ✓ | ✓ |
| D6 cuts a non-waivable control | ✓ | ✓ | ✓ | ✓ |
| **Total** | **4/6** | **4/6** | **6/6** | **6/6** |

**Two of the six defects flipped, consistently, and four did not.** The unit
here is the *defect*, not the class, and the two do not correspond. The six
defects map onto only four distinct classes — D1, D2 and D4 all sit in class 4,
D3 in class 3, D5 in class 2, D6 in class 6 — so class 4 both flipped (D4) and
did not (D1, D2), and **classes 1 and 5 were never sampled at all.** The
rubric's measured marginal contribution on this set is therefore two defects,
in two classes, out of four classes tested and six shipped. Nothing here
measures classes 1 or 5.

### Why the four made no difference

Arm A reached them through rules it already had, by a different route:

- **D1 and D2** fell to the universal-claim rule. Both control runs said to drop
  the bare count and name the mechanism that makes coverage exhaustive, which is
  the derivation in all but name.
- **D5** fell to the same rule from the other side: arm A called the criterion an
  unfalsifiable universal claim over an open set and prescribed a named closed
  corpus. It never said "holds on empty state". The defect was caught; the
  mechanism was not diagnosed, and arm B additionally required the signal to come
  from outside the implementation.
- **D6** fell to the existing deferral-and-`Follow-ons` rule, which ships in the
  same section arm A received.

That is a real finding about the rubric, not a null result to explain away: four
of its six classes are already reachable from shipped guidance, and their value
is diagnosis rather than detection.

### Why the two flipped

**What both share is absence from arm A's material** — neither the one-sided
contract nor the projection class appears in the shipped criterion-shape
guidance. Their standing in prior art differs, and only one is unmatched. The
[survey](spec-authoring-quality-survey.md) § 1 lists *targets a projection*
among the classes with no equivalent in any requirements-engineering frame. The
*one-sided contract* is not in that unmatched set: the same section records
EARS's unwanted-behaviour template as pairing a refusal with the positive path
that must still succeed, which is the concept's nearest prior art rather than
its absence. So the flip is explained by what arm A was given, not by the frame
mapping — which is also the argument the Confounds section below actually
rests on.

**D4 is the sharper result, because arm A did worse than miss it.** Neither
control run noticed that `build/audit-report.json` is generated output. Both then
wrote *new* criteria pinned to that path — one requiring the exit code to agree
with the file's contents, another constraining what may reach it. A control-arm
review would have shipped two additional criteria fixed to an artifact the next
build overwrites. Missing a class and then building on it are different costs.

## Unplanned observation: the control arm invented more scope

Not pre-registered, so treat it as a lead rather than a result. Arm A returned 12
and 13 findings; arm B returned 10 and 11. The extra findings were not extra
coverage. Both control runs demanded non-functional bars the draft never implied
— a wall-clock ceiling on a named runner, a dependency-scan threshold — and one
raised a limit-dominance problem conditioned on a parser ceiling the brief never
mentions. This is the reviewer-invented-remedy shape the deletion pass exists to
catch, and it points the same way as the finding that a longer instruction set is
not a stricter one.

## What this does not measure

- **Not the delivery mechanism.** Ablating a reference measures whether the
  *content* binds. Whether these classes belong in a skill reference read by the
  primary session, or in a dispatched authoring agent that receives them cold,
  is a different comparison. Answering it needs the authoring envelope
  `spec-author-agent.md` S1 owns, and both routes are now cheap to reach because
  coding harnesses can invoke headless instances. **Nothing here favours either
  route.**
- **Not authoring.** Both arms *reviewed* draft criteria. An author writing from
  a blank template is the population that matters, and it was not sampled.
- **Not defect outcome.** The score is whether a class was named, not whether the
  resulting spec shipped fewer defects. No design here can reach that.

## Confounds

- **Brief length differs by 1,830 words**, so an alternative explanation for D3
  and D4 is that more instruction text helped, irrespective of content. Two
  things argue against it and neither closes it: the flipped classes are exactly
  the two absent from arm A's material, and the longer arm returned *fewer*
  findings, which is the opposite of a volume effect. A length-matched placebo
  arm — arm A plus equally long irrelevant guidance — would settle it and was not
  run.
- **n = 2 per arm, one challenge set, one model, one session.** Four runs cannot
  separate a real effect from a consistent one.
- **The challenge set was written by the same session that wrote the rubric.** It
  seeds classes the rubric names, so it measures whether stated content binds and
  cannot discover a class neither artifact knows. It is an activation measurement,
  not a coverage one.

## Reproducing it

Rebuild both briefs from the shipped files, assert the control brief does not
contain `spec-authoring-rubric`, dispatch one fresh agent per run with the brief
path and a no-other-tool instruction, and score each return against the six
defects above with the conjunction split as the validity check. The arm briefs
are session scratch and deliberately not committed; the recipe, not the
artifact, is what survives.
