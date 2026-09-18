# Verification ledger — architect-design-scope-templates

Execution observations. The spec carries the contract; this file carries what
was actually run and seen.

## Manual verification — the subsystem template read end to end

**When:** 2026-09-18, after T1 landed.
**Why it is not a test assertion:** `test_document_model_contract.py` proves a
question mark is present and that the model marker precedes the rationale
marker. Neither shows that the question is one a designer can answer at that
zoom, which is the property the template exists for.

**Observed** in `assets/subsystem-design.md`, all eleven sections:

- Every section opens with a genuine interrogative, not a restated heading.
  Section 2 asks what the internal elements are, how they relate, and at what
  zoom — three linked questions a structural model actually answers.
- Every model-bearing section places its table or diagram before the prose.
  The rationale blocks explain the model rather than repeating it; section 4's
  asks why each invariant is load-bearing and what breaks silently downstream.
- Section 5 states the `stateless` rule twice — once as a literal table row and
  once in the rationale — so an absent row cannot be read as either answer.
- Section 6 says a topology diagram is drawn only when placement differs from
  the structural model, and to say so in prose otherwise. That is the check
  that stops section 6 repeating section 2.
- Section 11 tells the author to omit it entirely when empty rather than leave
  a heading with nothing under it.
- No appendix in any of the three templates.

**Verdict:** pass. The questions are answerable at the declared zoom.

## Description read — routing widening

**When:** recorded at T6.
**Why a read and not a run:** the description's routing boundary is pinned by
equality at both ends in `test_yagni_contract.py`, and the middle span is
deliberately unguarded. Bounding the middle would need either equality on the
whole description — the brittleness that pin removed — or an exhaustive list of
widening phrasings, which cannot converge. No test reaches a routing widening
inserted into the middle, so the check is a read.

**What changed in the middle span.** Five of the old middle's six claims are
carried unchanged: shapes a one-page concept first; Mermaid inline; converges
against review; and the cloud well-architected sentence, verbatim. Two changed:
the eight-section Google-style output became "authors from one of three
model-first templates chosen by architectural scope — a whole application or
system, one subsystem, or a change to an existing architecture — leading with
the structural, runtime, contract, data, deployment and quality models and
following each with its rationale"; and the "2-5 pages" claim is gone, because
it describes an output the skill no longer produces and a page range is the
kind of size figure this change refuses to ship.

**No trigger added.** The trigger list is a pinned span and is byte-unchanged.
The new middle introduces no trigger phrase of its own: the three scope names
sit in a clause about what the skill authors, not about when it fires.

**No new applicable situation.** The nearest candidate is "a change to an
existing architecture". It is not new: the unchanged invocation sentence
already covers "designing a system or integration", and the unchanged trigger
"what's the right way to build X" already reaches a change to an existing
system. What is new is that such a request now has a differentiated output
shape, not that the skill answers a request it previously declined. The
refusal clause still hands diagrams and critiques away, byte-unchanged, and
nothing in the new middle reaches toward current-state assessment.

**No authority added.** The middle says nothing about tools, write scope,
network access, or which gates fire. `metadata.boundaries` is unchanged and is
asserted exactly by the authority contract.

**Verdict:** no widening. This is a read, not a run — the test stays green
either way, which is why the finding is recorded here rather than claimed as
covered.

## Review — two lanes, ten rounds

Both lanes ran as Codex reviewer sessions with disjoint focus sets.

**Adversarial lane** (spec conformance, name fidelity, slice boundary,
citations, cross-file coherence, changelog): 8 sustained → 3 → 1 → 3 → 3 → 1 → 0.

**Quality lane** (test shape, cost to live with, coverage gaps, duplication,
the negative control): 0 blockers, 7 concerns, 2 nits. Six concerns and one nit
acted on; round 9 raised 2 fragility concerns, both closed; round 10 returned
the clean sentinel.

Every repair that touched a control was mutation-checked rather than assumed:

- The model-first control's domain moved out of the artifact under test after
  two rounds showed self-selection at successive levels. A heading-rename
  mutation proves the domain is independent.
- `_graded_items` was walked against thirteen evasions — bare marker, three
  comment forms, four fence forms, two indentation forms, two placeholder
  forms — and four legitimate forms, including the shipped two-word check
  `- [ ] No strawmen.` and a wrapped item.
- `_size_thresholds` was walked against eight threshold phrasings and four
  benign ones, after the first version false-positived on `more than one`.
- `_assert_model_first` was extracted so both mutation tests drive the
  production assertion. Gutting it now reds them; before, it did not.

## Accepted residue

- **A spelled-out threshold outside `WORD_NUMBERS`** — "thirteen pages" —
  passes the size scan. A number-word grammar is the only complete fix and the
  looser alternative reds on ordinary prose. Stated in the helper's docstring
  rather than overclaimed in the test name.
- **A task item nested four spaces under a parent list** is read as indented
  code by `_graded_items`. No shipped rubric item is nested; a future one reds
  its section by name rather than passing silently.
- **`packs/architect/tests/skills/architect-design/` does not run on a pull
  request.** `build-check.yml:433-434` runs only `.../tests/pack/` and
  `.../architect-assess/`; this directory appears only at `Makefile:610`. The
  three suites are proven by a dispatched `test-corpus` run. A later PR
  touching these files can merge green while breaking them.
