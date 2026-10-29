# Can the work-loop report completion?

**No.** The work stays incomplete. Passing feature tests are not enough. Six of the accepted preservation criteria have no evidence at all, and the work-loop's Finish checklist refuses to declare done until the accepted criteria are met.

## Why the feature tests do not count

The work-loop routes this case to `references/preservation-evidence.md`, because the accepted criteria include preservation properties. A preservation property names an existing behavior to keep, the change it allows, and an oracle (the check that compares what you got with what you expected). That reference lists four kinds of evidence that do not count:

- **Feature-only.** The creation tests prove only that the new synthetic value nodes exist. They do not prove that old behavior survived. This is the case here.
- **Missing.** No result exists for a family the criterion names. This is true for every preservation criterion here.
- **Stale.** The result was produced against a different revision.
- **Tautological.** The expected side reuses the code under test, or the oracle has no failing mutation.

The reference says: "A property short of supported blocks completion."

## What each criterion still needs

Each needs a result from the repository's own tests and gates. The expected side must come from outside the code under test: the base revision run on the same inputs, a reading of the input that never calls the implementation, or a table written in the criterion or test. Each oracle must also fail on a named single-edit mutation, recorded under `references/mutation-proof.md`.

| Accepted criterion | Evidence family | Proof still needed | Mutation the oracle must catch |
| --- | --- | --- | --- |
| Ordinary calls avoid synthetic targets | Conservation | Base and head call resolution on the same inputs agree, within the allowed change | Drop the step that keeps synthetic nodes out of call targets |
| Default search excludes values | Conservation | Base and head default search results agree; values appear only when explicitly asked for | Drop the default-search filter |
| Full and incremental builds agree | Equivalence | Full and incremental graphs compare equal, and the comparison is shown to tell two different graphs apart | Leave one member out of one build |
| A small edit stays within its invalidation bound | Bounded work | Edit one file, measure the work done, and report within or over budget against the bound the criterion states (no universal count) | Make invalidation cover the whole graph |
| Delete and rebuild paths remove values | Lifecycle | Create, update, delete, and rebuild through the production paths, with no dangling value nodes after removal | Skip the cleanup in one path |
| Supported external construction of the public result type compiles | Compatibility | Construct and unpack the public result type the supported ways, using the repository's own compiler or runtime | Change one signature or field that callers rely on |

## Missing tools lower nothing

adapt-to-project and code intelligence are not installed. Under the preservation-evidence reference, "An absent optional pack, code-intelligence feature, or benchmark tool lowers nothing." The `new-spec` shared-substrate reference also says the absence of code intelligence "removes no class." The work-loop also says not to add a new gate, harness, or tool for this evidence. If the repository's own seams cannot produce a family, that property stays unsatisfied until the owner narrows the criterion.

## What the work-loop does next

1. **DECIDE.** The missing evidence is **Required**, because it comes from accepted acceptance criteria. If it is included now, add the six evidence tasks to the plan and go back through GATES and REVIEW. If it is not included now, stop and report the work as incomplete. Only the owner can narrow or waive the criteria.
2. **Finish checklist.** "Acceptance criteria satisfied" fails while any preservation property lacks fresh, independent, mutation-proven evidence on the current revision. A green gate run, a merged PR, or review stasis does not change that.
3. **Completion report.** The work-loop may report the feature as implemented with its creation tests passing. It must also say that the work is not complete and that all six preservation properties are short of supported, for the reasons above.
