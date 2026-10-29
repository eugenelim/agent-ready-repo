# Shared-substrate preservation

A new member of something shared can break code that never mentions it. Add a
node kind to a graph, and every generic reader of that graph now sees it:
search, ranking, rebuilds, cleanup, and anything that serializes the graph. A
test that only proves the new member can be created passes while those readers
break.

Load this reference from step 3 when the predicate below fires. It tells you
how to find each existing behavior the change can disturb, and how to turn each
one into a criterion that fails if that behavior moves.

## When it fires

It fires when a proposed addition or change becomes a member of a model,
registry, graph, index, schema, namespace, or collection that existing generic
operations can observe without an explicit opt-in.

It does not fire in two cases. Confirm either one with repository evidence
before you rely on it:

- **A private helper with a single caller.** One reference search that finds
  only the definition and that caller settles it.
- **A new entity that every generic read path already excludes behind an
  explicit filter.** Cite the filter on each path. If any generic read path
  lacks the filter, the predicate fires.

When it does not fire, the ordinary step-3 anchors apply. Do not build a
consumer map or extra preservation criteria.

## Behavior classes

Check each class that the change can reach:

- direct readers and writers
- selection and resolution
- default search or presentation
- ranking and traversal
- full and alternate construction, such as full and incremental builds
- invalidation and update
- lifecycle and cleanup
- serialization
- supported public compatibility

## Finding consumers

Use repository-native evidence only:

- effective guidance;
- the substrate's definition and its writers;
- each path that reads it;
- constructors, serializers, and update paths;
- tests, manifests, compilers, and repository gates.

Start from the definition and follow each read path. An optional
code-intelligence capability may speed this up. Its absence removes no class,
and its answer is evidence, not a verdict.

## When to stop

Stop when every reachable class has a preservation criterion or a named gap.

- A class is unreachable only when the consumer map cites the search that found
  no reader.
- Do not dismiss a reachable class because the new member seems not to affect
  it. Give it a criterion that states the bound, or name a gap.
- Write a named gap in the spec's `## Assumptions`. It blocks review while it
  stands.

The rule counts behavior classes, never files or analogues.

## What a preservation criterion adds

`assets/spec.md` § Acceptance Criteria and
`references/spec-authoring-rubric.md` own criterion shape. Write each
preservation criterion under them. A preservation criterion adds four things:

1. **The old behavior** it keeps.
2. **Its allowed delta.** This is often none. When it is not none, name exactly
   what may change, such as "values appear only when explicitly requested".
3. **An oracle that fails if the behavior moves.** Take the expected side from
   the base revision, not from the implementation under test, wherever you can.
4. **A contradiction statement:** a sustained review finding against it
   contradicts it.

Some evidence looks like preservation but is not:

- A test that only proves the new member can be created says nothing about
  existing behavior.
- "Existing tests pass" names no behavior, no delta, and no oracle.
- A check that a public file is unchanged forbids the change instead of proving
  compatibility. A compatibility oracle exercises the supported construction or
  destructuring surface.

## Where the consumer map lives

The consumer map is task-local working material. Put it in the plan's
`## Design (LLD)` or in review notes, never in `spec.md`. Use one row per class:

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| <behavior class> | <path:line> | <criterion ID, or the named gap> |

The spec cites none of the map. Deleting or rebuilding it changes no criterion,
so it cannot change accepted scope or the acceptance verdict.

## A consumer found later

A consumer found after approval may change accepted behavior, scope, a public
contract, a durable output, or accepted risk. If it does, it takes the
controlled amendment and fresh review. A discovery that changes only task
order, local method, or test shape stays plan-level: it goes into the plan
before approval, or the verification ledger after, and gains no approval
authority.
