# Preservation evidence

Some work adds a member to a structure that shared code reads, such as a new node kind or a new registry entry. A preservation property says an existing behavior must survive that change. This reference covers the evidence that shows the property holds.

## When it loads

Load it when the accepted criteria include a preservation property. Such a criterion names an existing behavior to keep, the change it allows, and an oracle. An oracle is the check that compares what you got with what you expected.

The [shared-substrate preservation reference](../../new-spec/references/shared-substrate-preservation.md) owns how these criteria are written. This reference owns the evidence that satisfies them.

## What makes evidence independent

The expected side of the oracle must not come from the code under test. Take it from one of these:

- the base revision, run over the same inputs;
- a reading of the input that never calls the implementation;
- a table written out in the criterion or the test.

An oracle also has to fail when the property breaks. Pick one single-edit mutation that removes the property. Run the oracle against it. An oracle counts only after it fails on a named mutation. Record the run with the proof record in [mutation proof](mutation-proof.md). An oracle that still passes under its mutation is not evidence.

The evaluator reads only the receipt's term, outcome, and freshness. So independence has to hold where the receipt is produced. Emit a passing outcome only when the oracle passes on the implementation under test and fails on its mutant.

## The five families

Each family answers one question. Cover every family the criterion names.

- **Conservation.** Run base and head over the same inputs. Compare the results inside the allowed change. Mutate by dropping the step that keeps the old result.
- **Equivalence.** Say what "the same" means outside the evidence. Compare full and incremental (or alternate) construction. Show that the comparison can tell two different results apart. Mutate by leaving one member out of one build.
- **Lifecycle.** Create, update, delete, and rebuild through the production paths. Check that nothing dangles after removal. Mutate by skipping the cleanup in one path.
- **Compatibility.** Use the supported ways to construct and unpack the structure. Run them with the repository's own compiler or runtime. Mutate by changing one signature or field the callers rely on.
- **Bounded work.** Edit one file and measure the work done. Report a command result, within or over budget, against the bound the criterion states. Never use a universal count. Mutate by making the work cover the whole structure.

## Through existing seams

Use the repository's own tests and gates. Record each result against the current subject, the revision you are finishing. Do not add a gate, harness, or tool for this.

An absent optional pack, code-intelligence feature, or benchmark tool lowers nothing. If a family cannot be produced with what the repository has, the property stays unsatisfied. It stays that way until the owner narrows the criterion.

## When the work stays incomplete

Four kinds of evidence do not count:

- **Missing.** No result exists for a family the criterion names.
- **Stale.** The result was produced against a subject other than the current one.
- **Tautological.** The expected side reuses the implementation, or the oracle has no failing mutation.
- **Feature-only.** It proves only that the new member exists, not that old behavior survived.

Each one leaves the property short of supported. A property short of supported blocks completion.
