# Projected-tree planning doctrine

- **Status:** Draft
- **Level:** feature

## Outcome

A plan for a change to a corpus that ships compiled is written against the tree
the guards actually read. Today a planner can enumerate authored sources, pass
every check they thought of, and still author criteria that cannot be satisfied
until a recompile happens — which they find out during execution, as an
amendment.

## The opportunity

Some guards read authored sources and some read the compiled projection, and
nothing tells a planner which is which. Two owner-authorized amendments in one
delivery came from that single blind spot. The anchor-test sweep checked digests
and counts over authored sources, while two shipped guards scan the projection:
one requires a doctrine group's provenance block to appear in the compiled body,
so the first task adding such a group cannot pass without a recompile; the other
forbids delivery-mechanic literals anywhere in the projected tree, so a
criterion requiring one was unsatisfiable and only failed once the recompile
made it visible.

A third consequence follows. Because the compiled source digest binds recorded
evaluation runs, the recompile and the re-measurement have to travel inside the
same task as the last authored edit — a later task can never share its wave, and
gates run at wave boundaries.

## What would have to be true

Before tasks are written over a compiled corpus, the planner can tell which
guards read the projection and which read the source, and places the recompile
in the task that makes the last authored edit.

Getting there needs a decision this intent does not make: whether the guard
split is knowable mechanically — derived from what each check opens — or whether
it is doctrine a maintainer states and keeps current. The mechanical route is
worth more and costs more.

## Boundary

Placement is open. The rule spans two owners and belongs to whichever is
decided, not to both:

- `packs/AGENTS.md` owns authoring inside a pack that ships compiled, and was
  the destination the observation suggested.
- `work-loop` owns wave and gate mechanics, which is what the
  recompile-inside-the-last-task half is actually about.

Splitting the rule across both would reproduce the duplication problem the
authoring rubric warns about, so this needs one home.

## Provenance

Mechanism and measurement are recorded as captured observation
`kco-202609-3f7fc5a7b47a27460eb6d6f831de80119400924c8dd9b5d5fa09b2c88f863bc8`
in `docs/knowledge/observations/gotcha/2026-09.jsonl`, distilled to topic
`plan-a-corpus-change-against-the-projected-tree-not-the-authored-one`.
