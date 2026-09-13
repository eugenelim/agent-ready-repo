# Answer: large-mixed (neutral-grammar)

## F1
Accept. The governing-authority metadata will name RFC-0077 rather than say that there is no constraint, and AC3 will be retained only as the RFC-0077 same-or-ancestor rule. That removes the contradictory scope direction while preserving the intended ancestor-only contract.

## F2
Accept. AC4 will say only that the pre-truncation number of matches is non-increasing as a query narrows. It will not imply that the independently sorted and envelope-truncated returned sets are nested, because that property is not guaranteed by the selection algorithm.

## F3
Accept. Enquiry will receive its own matcher path, while `_pending_from_loaded_partitions` keeps the existing matcher and journal-capacity behavior. The plan and tests will cover those callers separately, which preserves ADR-0082's mode isolation.

## F4
Accept. The version-bump criterion will explicitly require the corresponding changelog entry in the same pull request, alongside the pack and plugin version files. That makes the convention, RFC-0095, and `packs/AGENTS.local.md` obligation enforceable.

## F5
Accept. T4 will compare the migrated atom sequence with an independently derived expected sequence from the original stored text, rather than applying the candidate splitter to both sides. It will also exercise the sanctioned writer with duplicate atoms and assert that it refuses them, so neither a faulty splitter nor silent deduplication can pass.

## F6
Accept. T4 will establish one repository path for its before-and-after migration record before the migration runs, and will write both measurements there. This makes the required evidence reviewable instead of leaving it as an unlocated process claim.

## F7
Accept. The ranking contract and TDD table will define `.` as corpus-wide and least specific. Specificity will be normalized across the corpus's path, glob, and root forms so base reduction alone cannot promote a root expression above a path-bounded expression.

## F8
Accept. T4 will migrate every topic through `write_topic`, not direct file writes. That retains RFC-0077's scope validation and writer lock for every changed topic.

## F9
Accept. The migration will not retain comma-joined or glob syntax as accepted scope atoms. For every affected legacy value, the migration record will state its derivation to valid repository-relative path atoms; entries without such a derivation will be stopped for review rather than silently migrated.

## F10
Accept. The revision will designate one authoritative source for each load-bearing value and replace repeated normative statements with references to it. In particular, the version-bump conclusion, legacy-topic count, `enquiry_bodies` limit, and other such facts will have a single authoritative statement, with any remaining occurrences clearly evidentiary rather than normative.

## F11
Accept. The delivery record will describe the repair and matcher work as proposed until it has actually happened. Historical measurements will remain labelled baseline evidence, and no section will present a planned migration, rebuild, projection, or verification as completed.

## F12
Accept. The Objective's success condition will be the observable production-matcher result already suitable for AC1: every active topic matches at least one concrete repository-path query. The hand-grep comparison will be removed because it has no derivable verification.

## F13
Accept. The root-scope wording in the relevant acceptance criterion will use `corpus-wide`, matching the Objective, rather than describe empty-base reduction. Base reduction remains an implementation and test concern, not a contract term.

## F14
Accept. T7 will cite the pending-selection non-regression criterion and the full `project-knowledge` suite criterion that it actually discharges. This restores traceability for both the isolated pending behavior and the suite gate.

## F15
Accept. T2 and T5 will explicitly use TDD for enquiry matching and specificity ranking. T6 will gain a Testing Strategy row that assigns TDD to enquiry exclusions, with independently failing exclusion cases, so all three tasks have an unambiguous verification mode.

## Acceptance-criteria count after these decisions
15, from a starting count of 15.
