# Amendment 005 — the razor criteria move to the task that builds the dispatch

**Authorised by:** eugenelim, 2026-09-20 (same standing authority as 001-004)
**Against:** approved_plan_hash c676c208a2b5

## The defect

Three criteria sit in T5's `Tests:` and cannot be discharged there:

- the instruction-shape refusal, asserted **before** the reasoning dispatch
  and proven by a dispatch spy recording zero calls;
- the necessity razor's refusal;
- the shape-threshold judgement.

All three are assertions **about a reasoning dispatch**. T5 owns the
validator and its tests; it owns no work-loop file, and the dispatch is
invoked from the close. T7 builds it: the dispatch spy, the input set that
excludes the transcript, the parameter enumeration, and the data delimiter
are all T7's. T5 runs in the wave before T7.

So the plan asks T5 to spy on something that does not exist until the next
wave. This is amendment 002's shape again — a criterion in a task that
cannot reach what the criterion names.

**Not caused by the controller's narrowing.** The T5 brief did narrow its
scope to the derived field set and the per-element scan assertion. Even
without that narrowing T5 could not have built the dispatch, because it holds
no work-loop file.

## The amendment

Move the three criteria from T5 to **T7**, which builds the dispatch they
assert against and already holds every other dispatch criterion. T7's
`Touches:` is a superset of T5's plus the work-loop files, so nothing needs
widening. No criterion changes. No wave placement changes.

T5 keeps what it proved: the derived scanned field set, the per-element scan
assertion, and the catalog quantification.

## Standing instruction this produces

A criterion that asserts a behaviour of some mechanism belongs in the task
that builds that mechanism, not the task that owns the file the mechanism
happens to live near. Check the dependency direction before placing an
assertion, not just the file list.
