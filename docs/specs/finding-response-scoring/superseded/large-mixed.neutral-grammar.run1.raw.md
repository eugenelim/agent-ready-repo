# Answer: large-mixed (neutral-grammar)

## F1
Amend the authority declaration and the matching contract to name RFC-0077 as the governing authority and to state only same-or-ancestor matching. This removes the contradictory `none` claim and prevents a descendant match from becoming an implied extension of the contract.

## F2
Amend AC4 so it guarantees only that the pre-envelope match count is non-increasing as a query narrows. Do not promise nested returned sets, because the query-independent ordering and the bounded envelope cannot provide that property.

## F3
Give enquiry its own matcher and leave the pending caller on its present matcher. Amend the pending-path non-regression criterion to require independent coverage of both callers, including journal-capacity processing, because ADR-0082 makes their authorities separate.

## F4
Amend the version-bump criterion to require the changelog entry in the same pull request. A patch version is not complete under the repository conventions, RFC-0095, and `packs/AGENTS.local.md` without that entry.

## F5
Change plan task T4 to compare the persisted post-migration atom sequence with an independently captured pre-migration sequence, rather than applying the splitter to both operands. Add a sanctioned-writer test that supplies duplicate input and proves it is refused. This demonstrates fidelity and preserves the writer's duplicate protection.

## F6
Change plan task T4 to name one exact repository path for its before-and-after record before migration starts. The process criterion needs a durable, reviewable artifact rather than an unstated execution note.

## F7
Define `.` and every empty-base glob as corpus-wide with the same lowest specificity. Amend the ranking contract and its tests to use that rule, so neither root form can outrank path-bounded scopes.

## F8
Change plan task T4 to perform every topic update through `write_topic`. That is the RFC-0077-sanctioned route and retains both scope validation and the writer lock.

## F9
Replace the proposed comma splitting and glob preservation with a migration that writes only RFC-0077-valid repository-relative path atoms. Require a recorded derivation for every former comma-joined or glob scope. This repairs the data without making unsupported syntax part of the lasting contract.

## F10
Consolidate each load-bearing value in one authoritative location and have the other document link to it rather than restate it. This includes the version-bump conclusion, the 30-topic count, `enquiry_bodies=12`, and all comparable facts, so future updates have one normative source.

## F11
Rewrite retrospective wording as present baseline evidence or as proposed work, as appropriate. The delivery record must not state that an unimplemented migration, matcher change, or verification has already happened.

## F12
Amend the Objective to use the observable success condition: every active topic matches at least one concrete repository-path query through the production matcher. Make AC1 and its integration test the verification for that condition; hand-grepping is not a testable completion signal.

## F13
Replace the plan-owned phrase about reduction to an empty base in AC6 with the contract term `corpus-wide`. The implementation may still calculate bases internally, but the acceptance criterion should state the user-visible semantic rule.

## F14
Correct plan task T7's references to AC11 and AC12. Those are the criteria for unchanged pending selection and the full project-knowledge suite, respectively, so the task remains traceable to both obligations.

## F15
Add explicit verification modes to plan tasks T2, T5, and T6: TDD for enquiry matching, TDD for specificity ranking, and TDD for enquiry exclusions. Add the missing Testing Strategy row for exclusions, with independently failing cases, so the plan has an unambiguous test obligation.

## Acceptance-criteria count after these decisions
15, from a starting count of 15.
