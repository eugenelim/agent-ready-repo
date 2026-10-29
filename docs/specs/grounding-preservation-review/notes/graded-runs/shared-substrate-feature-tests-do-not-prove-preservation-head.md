# Can the work-loop report completion?

**No.** The work-loop must refuse to declare done. Every preservation property except creation itself is unsupported, and an unsupported preservation property blocks completion.

## Why

The accepted criteria include preservation properties. Each one names an old behavior to keep, its allowed change, and an oracle (the check that compares the actual result with the expected one). That fires the routing row in `work-loop/SKILL.md` § Conditional-reference routing, which loads `references/preservation-evidence.md`.

That reference says four kinds of evidence do not count: missing, stale, tautological, and feature-only. "Each one leaves the property short of supported. A property short of supported blocks completion."

The only evidence here is the feature creation tests. They prove the new synthetic value node exists. That is **feature-only** evidence. For every other named property no result exists at all, which makes it **missing**. Passing feature tests are gates, and the SKILL.md anti-pattern "Declaring victory because gates pass" applies: gates are necessary, not sufficient.

So the first Finish-checklist assertion, **Acceptance criteria satisfied**, fails. The intent is not complete, and its owner has not narrowed or waived it.

## What each criterion still needs

Each oracle needs an independent expected side: the base revision run on the same inputs, a reading of the input that never calls the implementation, or a table written in the criterion or test. It counts only after it fails on a named single-edit mutation, recorded per `references/mutation-proof.md`. Every result must be recorded against the current subject, the revision being finished.

| Criterion | Family | Evidence now | Needed proof and mutation |
| --- | --- | --- | --- |
| Ordinary calls avoid synthetic targets | Conservation (selection and resolution) | Missing | Base vs head call resolution on the same inputs; mutate by dropping the step that excludes value nodes from call targets |
| Default search excludes values | Conservation (default search) | Missing | Base vs head default search results, values appear only when explicitly requested; mutate by removing the default filter |
| Full and incremental builds agree | Equivalence | Missing | Compare full and incremental graphs under a stated "same" that can tell two different graphs apart; mutate by leaving one member out of one build |
| A small edit stays within its invalidation bound | Bounded work | Missing | Edit one file, report a command result within or over the bound the criterion states (no universal count); mutate by making invalidation cover the whole graph |
| Delete and rebuild remove values | Lifecycle | Missing | Create, update, delete, rebuild through production paths, check nothing dangles; mutate by skipping cleanup in one path |
| Supported external construction of the public result type compiles | Compatibility | Missing | Construct and unpack the result type the supported ways with the repository's own compiler or runtime; mutate by changing one field or signature callers rely on |
| Value nodes can be created | (feature behavior) | Feature tests pass | Already shown, but it proves no preservation property |

## The missing tools change nothing

The missing adapt-to-project pack and code intelligence do not lower the bar. `preservation-evidence.md` says: "An absent optional pack, code-intelligence feature, or benchmark tool lowers nothing. If a family cannot be produced with what the repository has, the property stays unsatisfied." The evidence has to come through the repository's own tests and gates. The work-loop must not add a new gate, harness, or tool for it.

## Next step

There are two allowed paths:

1. **Preferred:** write the preservation oracles with the repository's existing test seams. Run each against the head and its named mutant, and record the results against the current revision.
2. Ask the criteria owner to explicitly narrow or waive a criterion that cannot be proved with what the repository has. Until they do, the work stays incomplete, and the run surfaces the gap instead of reporting done.
