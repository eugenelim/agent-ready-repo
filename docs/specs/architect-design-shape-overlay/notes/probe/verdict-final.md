# Overlay probe — verdict, after the control

## The bar, quoted verbatim and unedited

> Kill the overlay if a reviewer who did not write it judges that the overlay's
> added content is not load-bearing, or if the routed document grows without a
> named concern that the unrouted one missed. Growth alone is not a pass, and a
> concern the author would have raised anyway is not a find.

## What was run

| Pair | Arms | Router difference | Judge |
| --- | --- | --- | --- |
| Treatment | A vs B | unrouted vs **routed** | Codex, blind |
| Control | A vs C | **none — both unrouted** | Codex, blind, identical question |

A fourth arm, D, was authored by Codex against the pre-axis router as the
baseline half of a cross-family pair; its routed partner was stopped once the
control returned, so no judgment used it. `arms.txt` records why it is kept.

Arms A, B and C are Claude-authored against the same frozen brief. Arm C was
authored against commit `7c794b79`, byte-identical to what arm A saw, so the control's only
difference from the treatment is that *nothing changed between its two arms*.

## Result

| Measure | Treatment (A vs B) | Control (A vs C) |
| --- | --- | --- |
| Concerns unique to first arm | 5, load-bearing | **9, load-bearing** |
| Concerns unique to second arm | 6, load-bearing | **6, load-bearing** |
| Total differing concerns | 11 | **15** |
| Word-count difference (see item 4) | 19 | 48 |

**Two runs that differ in nothing diverge more than the run that carries the
overlay.** The conclusion rests on the concern counts, 11 against 15. The
word-count row is shown for completeness and carries no weight: all three arms
in it are pinned at the `DA10` ceiling (item 4), so what differs between them
is how much markup the shell counts and the gate does not — counting-rule
residue, not a measure of anything the probe is testing.

## Sequence, disclosed because it bears on weight

The control pair was **not** part of the original design. The treatment pair ran
first, returned a symmetric result, and the control was added in response to it,
to test whether that symmetry was the overlay or the author. The control is
therefore post-hoc. It is reported anyway, and it is decisive in the direction
that weakens the delivery's own case rather than strengthening it, which is the
direction a post-hoc control is least likely to be motivated toward. A reader
weighing whether to fund the follow-on study should know the ordering without
having to open `method.md`.

## Verdict

**The predeclared kill condition is not answerable by this experiment.**

Read literally, neither limb fires and the overlay "survives": the judge called
the routed arm's added content load-bearing, and named concerns the baseline
missed. But the control returns the same answer when there is no overlay at all.
An instrument that reports "load-bearing concerns were added" for two identical
conditions is not measuring the overlay; it is measuring the spread of the
author. Reporting `survived` from it would be reporting an artifact, and the
bar's own qualifier — *a concern the author would have raised anyway is not a
find* — is precisely what the control demonstrates at scale: every one of the
nine A-only concerns in the control is, by construction, a concern this author
raises anyway.

So the honest disposition is neither `survived` nor `killed`. The bet is
**untested**, and the bar stands unedited for whatever experiment can test it.

## What is nonetheless established

1. **The axis works mechanically.** The routed run loaded three shape lenses —
   event-driven, distributed-services, layered-and-modular — where the pre-axis
   router could reach none. The multi-shape rule fired on its first real run.
2. **No claim is made about what the overlay does to document length.** The
   19-word treatment difference and 48-word control difference are
   counting-rule residue between arms pinned at the same ceiling, as the
   Result table says. They cannot support a positive finding on the intent's "longer not better" assumption, because
   they come from the same n=1 comparison this verdict disqualifies, and
   because both arms wrote to the `DA10` ceiling (item 4) — so the ceiling, not
   the overlay, is what bounded them.
3. **The specified passage-diff instrument is unsound**, and so is the
   concern-diff instrument that replaced it — for the same reason, now measured
   rather than argued.
4. **`DA10` calibration gains four re-derivable data points.**
   `check_document_architecture.py` over the committed arms, against its
   `WORD_BOUND` of 3300: **arm A 3300, arm B 3298, arm C 3295, arm D 2728**.
   The three Claude arms land within five gate-words of the bound. `wc -w`
   gives 3854 / 3873 / 3902 / 3275, so the gate excludes 554 / 575 / 607 / 547
   words of markup the shell counts. Two things follow for
   `architect-design-gate-calibration`, stated to the four points and no
   further: the three arms sharing one author cluster within five gate-words
   of the bound, while the one arm from a different author family lands 572
   gate-words (17%) below it — so clustering at the ceiling is an
   author-specific behaviour on this evidence, not a property of authors in
   general. And the gate's counting rule is what all four correctly wrote to;
   an earlier draft of this record called that a mis-measurement, which
   running the gate refutes.

## What would test the bet

The failure is n=1 against a noisy author. A discriminating design needs the
treatment difference to exceed the control spread — several pairs per condition
with the same judge and the same brief, reporting whether routed-vs-unrouted
divergence is distinguishable from unrouted-vs-unrouted divergence. That is a
measurement study, not a spec, and it is materially more expensive than the
overlay it would justify.

## Consequence for S2 and S3

They are gated on a surviving verdict. There is no surviving verdict — there is
no verdict. Contracting them on this evidence would rest two slices on an
instrument shown here to return the same answer whether or not the treatment is
present.
