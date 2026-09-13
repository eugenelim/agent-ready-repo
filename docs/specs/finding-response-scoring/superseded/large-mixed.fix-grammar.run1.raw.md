# Answer: large-mixed (fix-grammar)

## F1
Accept. The constraint record must name RFC-0077, and AC3 must state its one-way rule without ambiguity: a declared scope matches an equal or descendant query, while a strict descendant declared scope does not match its ancestor query. This aligns the contract, its cited authority, and the test.

## F2
Accept. Replace AC4's result-set claim with the measurable pre-truncation invariant: the number of matches cannot increase as a query narrows along a nested path chain. Selection is separately bounded and sorted, so it cannot promise nested returned sets.

## F3
Accept. Introduce an enquiry-only matcher for the changed resolution semantics. Keep `_pending_from_loaded_partitions` on the existing matcher, and test the enquiry and pending callers independently. This preserves ADR-0082's mode isolation and prevents a scope-reachability change from altering journal-capacity processing.

## F4
Accept. Amend the version-bump acceptance criterion to require the matching patch-version changelog entry in `docs/product/changelog.md` in the same pull request. A release version is incomplete without the required changelog record.

## F5
Accept. Replace T4's self-derived set assertion with hand-authored ordered expected atoms that exercise the sanctioned writer. Include duplicate input and assert refusal. The new test can detect an incorrect splitter and verifies the writer's no-deduplication contract.

## F6
Accept. Add the exact repository path of the AC9 before-and-after record to T4. Naming the artifact makes the process requirement reviewable and recoverable.

## F7
Accept. Define `.` and every glob whose base is empty as corpus-wide, with one shared lowest specificity. This makes ranking reflect the Objective rather than an incidental segment count.

## F8
Accept. Change T4 so every topic change goes through `write_topic`, including its validation and writer lock. That is the required RFC-0077 mutation boundary and prevents the migration from bypassing store invariants.

## F9
Accept. Revise the migration so both comma-joined values and glob values become valid repository-relative path atoms. Record the derivation for every replacement. The migration must not preserve unsupported syntax merely because it is already present.

## F10
Accept. Make one normative location the source for each load-bearing fact, including the version-bump conclusion, the 30-topic count, and the `enquiry_bodies=12` limit. Replace repeated statements with references to that location so later repairs cannot diverge.

## F11
Accept. Rewrite the identified passages as proposed work or baseline evidence. The specification must not describe its proposed implementation and migration as completed history.

## F12
Accept. Replace the hand-grep success claim with the observable production-matcher condition: every active topic matches at least one concrete repository-path query. That condition has a direct integration test and does not depend on a maintainer's informal search process.

## F13
Accept. Replace the plan-owned phrase `reduces to an empty base` in AC6 with `corpus-wide`. The acceptance criterion should use the specification's defined contract term rather than expose a particular implementation mechanism.

## F14
Accept. Correct T7's references to AC11 and AC12. Those are the criteria T7 actually verifies, so the repaired references keep the plan traceable to its contract.

## F15
Accept. Give T2, T5, and T6 explicit verification modes, and add a Testing Strategy row for T6's behavior. Each planned behavior then has a declared test or goal-based verification route.

## Acceptance-criteria count after these decisions
16, from a starting count of 15.
