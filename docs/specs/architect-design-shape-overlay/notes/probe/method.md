# Overlay probe — method record

**Scope of this header's pre-registration claim.** Except for the post-run
correction immediately below, everything down to and including *Known validity
limits* was written before any arm was authored, per the intent's second
validation hook. Everything from *Who authors each arm*
onward was added as the run proceeded — the arm freeze records after each arm
returned, and the control-pair rationale after the treatment pair's result was
seen. `verdict-final.md` § Sequence states the same ordering.

**One pre-registered statement did not hold, and is left unedited.** *Routed
arm* below says the routed arm is authored against the shipped region. Arm B
was authored against T1's working-tree draft of that region, and review
changed two sentences in it afterwards. *Control pair* records both changes
and what they cost the probe. Editing the pre-registered text would destroy
the thing that makes it pre-registration, so it stands and this note carries
the correction.

This is a spike: no spec, and no shipped file was changed by it.

## Baseline mechanism (the unrouted arm)

The unrouted arm is authored against `packs/architect/.apm/skills/architect-design/SKILL.md`
as it stands on the recorded revision below, which carries no system-shape axis.
This is the mechanism the hook asks to be named, and it is chosen because it is
the only one that needs no reconstruction: before S1 merges, the shipped router
genuinely has no axis, so the baseline is the real artifact rather than a pinned
old revision or a scratch copy with the region removed.

Consequence of the ordering: the baseline must be authored and frozen now. Once
S1 lands, this mechanism is no longer available and the hook's alternatives —
a pinned pre-S1 revision, or marker-region removal in a scratch copy — are what
remain.

## Routed arm

Authored after T1 lands, against the shipped marker-delimited region in the same
file. Deliberately not authored against a scratch paraphrase of the axis: round 8
of the spec review found that nothing otherwise binds the with-overlay run to the
region the pack actually ships, which would make the probe measure an instruction
written for the probe.

## Bar

The intent's predeclared kill condition, unedited. `DA3` and `DA10` are barred as
instruments: their bounds are uncalibrated, so a verdict read off them reads clean
whichever way the bound is wrong.

## Known validity limits, recorded before the result

Round 8 of the spec review established three questions this spike answers by
running rather than by specification, and they are recorded here so the verdict
is read at its real weight:

1. Whether a passage diff is a sound proxy for "a concern the unrouted one
   missed". A concern raised under a different heading, or in different words,
   is still raised.
2. Whether the routed document is identifiable from its own vocabulary, which
   would defeat a blind comparison however the documents are labelled.
3. Both arms are authored by one model, so the probe measures what the overlay
   changes in that model's output, not in an author's generally.

## Who authors each arm, and why not the session controller

Both arms are authored by fresh subagent contexts, not by the session running
the spike. The controller read
`packs/architect/okf/architecture-lenses/concepts/system-shapes/event-driven-and-streaming.md`
early in this session while grounding the spec. A baseline authored by that
context carries the overlay's concerns already, which shrinks the routed-extras
set and biases toward a kill — the safe direction, but a contaminated
instrument either way.

Each arm therefore gets a context that has read neither this conversation nor
the other arm. Symmetric by construction: the difference between the two runs is
the router's state, not the author's memory.

The controller still assembles the dispatch, so the controller's knowledge can
reach the arms through the brief. The brief is committed alongside the designs
for exactly that reason.

## Arm A — baseline, frozen 2026-09-20T08:28Z

- Authored by a fresh context against the skill at `7c794b79341313f8b6832d36db5df5ef4e27114d`, which carries no system-shape axis.
- Resolved scope: subsystem. One document; the decomposition rubric produced no child meeting `D1` plus another criterion.
- Concepts loaded, 9: four quality lenses (reliability, data integrity, operability, security), three foundations (tradeoffs, quality-attribute scenarios, decisions and cross-cutting concerns), provider-and-platform operating models, and source-detection confidence. **No system-shape concept** — there is no axis to route one.
- Shape: 391 lines, 3854 words, 11 sections, 4 Mermaid diagrams.
- SHA-256 (first 32): 099132f573c52ecb4d0540f110362fd3
- No repository file changed.

## Arm B — routed, frozen 2026-09-20T09:07Z

- Authored by a fresh context against the same `SKILL.md`, now carrying T1's shape-axis region (verified present, markers ordered, 149 tests green).
- Same resolved scope: subsystem, one document, same template.
- Concepts loaded, 11: the same eight as arm A minus enterprise-knowledge source-detection (no surface detected this run), **plus three shape lenses** — `system-shapes/event-driven-and-streaming.md`, `system-shapes/distributed-services.md`, `system-shapes/layered-and-modular-application.md`.
- Shape: 409 lines, 3873 words, 11 sections, 4 Mermaid diagrams. SHA-256 (first 32): d759f9eea05f1ff9e4ed654f2c2fe0f5

## Findings available before any judgment

**1. The axis fired, and fired multiply.** Arm A could reach no system-shape concept; arm B loaded three. The multi-shape rule — a design with an open decision in each of several shapes loads every one — was exercised on its first real run rather than sitting untested.

**2. No claim is made here about the overlay and document length.** `verdict-final.md` owns the disposition of the 19-word difference.

**3. The three Claude arms wrote to the DA10 bound, and every author measured it correctly.** `check_document_architecture.py` over the committed arms gives 3300, 3298, 3295 and 2728 against a `WORD_BOUND` of 3300 — the three Claude arms land within five gate-words of the ceiling. `wc -w` gives 3854, 3873, 3902 and 3275; the two rules differ because the gate excludes markup the shell counts, by 554, 575, 607 and 547 words respectively. The authors read the gate right, and a length comparison between arms measures the ceiling rather than the overlay.

**4. The passage diff does not measure what the kill condition asks.** 37 passages are unique to arm A and 43 to arm B, spread across all eleven sections. Two independent generations of one brief differ nearly everywhere, so "passage present in the routed document and absent from the baseline" counts rephrasings, not concerns. The kill condition asks for "a named concern that the unrouted one missed", which is a semantic comparison; the passage diff is a textual one. This is the validity question recorded in this file before the arms were authored, now answered by running: **the specified instrument is unsound, and the judgment must be posed as a concern-level comparison instead.**

## Control pair — why, and how the baseline was produced

Pair 1 returned a symmetric result: both arms' unique concern sets judged
load-bearing. Symmetry is what run-to-run variance looks like, so pair 1 cannot
attribute its difference to the overlay. A second routed/unrouted pair on a new
problem would give n=2 of the same confounded comparison; it would not separate
variance from effect.

The control does. Arm C is a **second unrouted run of the same problem**. If
arm A and arm C also differ by symmetric load-bearing concern sets, variance
dominates and pair 1's `survived` is uninformative. If they differ far less
than A and B did, the overlay's contribution is real and pair 1's symmetry has
another cause. One authoring run answers this, because arm A already exists.

**Baseline mechanism, per the intent's second validation hook.** T1's shape-axis
region was uncommitted while the probe ran, so the repository head at that
time — commit `7c794b79341313f8b6832d36db5df5ef4e27114d` — was the pre-axis
router. Arm C was authored against those exact bytes, restored with
`git checkout -- SKILL.md` — the bytes arm A saw, not a reconstruction and not a marker-region deletion that could leave residue. A
first attempt at deletion left one stray blank line, which `git diff` caught;
the checkout is byte-exact instead.
T1's region was restored, byte-exact, after arm C returned.

**Arm B's router is not the delivered router, and an earlier draft of this
record wrongly said it was.** Arm B was authored against `SKILL.md` at SHA-256
`604962f3552350d075ddd4041a6c7f85740c191357d5db8b111862dce21b8e0a`.

**No digest for the delivered file is recorded here, deliberately.** Two
earlier drafts pinned one and both went stale on the next edit to the region —
the second within the same review cycle that wrote it. A reader comparing the
two states runs
`shasum -a 256 packs/architect/.apm/skills/architect-design/SKILL.md` against
the digest above; a literal in this file cannot stay true while the file it
describes is still being edited.

Two sentences inside the shape-axis region differ, both changed by review
after arm B was authored, and both still true of the delivered region:
arm B saw the receipt value recorded "in the Stage-0 completion receipt
below", which names the wrong receipt — the skill puts selected concept paths
in the *working* receipt — and the shipped region says so instead. Arm B also
saw "for each shape whose routing signals the proposal matches", which asks an
author to match signals the category index does not carry; the shipped region
says to read the titles, open only the plausible shapes, and confirm against
each concept's own routing-signals section.

What that costs the probe: the routed arm read a region whose selection rule,
descent path, multi-shape rule and whole-load rule are identical to the
shipped ones, and which differs only in where a diagnostic value is written
and in how the index is described. Nothing arm B loaded or declined to load
turns on either sentence. But the two are not the same bytes, and a reader
re-deriving this evidence should know the treatment arm read a superseded
draft of the region.

## `added-passages.py` — what it was, and why its numbers are not the verdict

Run once, as `python3 added-passages.py arm-a.md arm-b.md`, from this
directory. It reported 37 passages unique to arm A and 43 unique to arm B,
across all eleven spine sections.

That output is the evidence for finding 4 above — it is what established that
a passage diff counts rephrasings rather than concerns, and therefore that the
instrument four review rounds had specified was unsound. The verdict does not
rest on these numbers; it rests on the 11-against-15 concern counts in
`judgment-treatment.md` and `judgment-control.md`.

The script ships because the finding it produced is load-bearing and a reader
should be able to reproduce it. It is not a general tool: it takes two
positional paths and raises `IndexError` without them.
