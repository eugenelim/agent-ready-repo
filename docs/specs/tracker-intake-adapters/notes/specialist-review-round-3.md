# Specialist implementation review — round 3

## Concerns

**1. SAST/SCA coverage is degraded and needs an explicit accepted-risk record.** `docs/specs/tracker-intake-adapters/notes/resolve-vs-surface.md:31`

The security finding is accepted for documentation before the human gate. The
quality review's request to check acceptance criteria is a lifecycle action,
not an implementation finding: work-loop requires the spec to remain
`Implementing` until all warranted reviewers are clean, then marks it
`Shipped` immediately before `reviewers-clean`.
