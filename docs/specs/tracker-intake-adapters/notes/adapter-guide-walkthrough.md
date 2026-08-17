# Adapter guide walkthrough

- **Review date:** 2026-08-16
- **Reviewer:** work-loop operator
- **Session boundary:** work-loop run `53948753-2885-477f-aa10-978578b1faf9`, T7 documentation wave
- **Scope:** shared tracker selection and vocabulary, Jira task guide, Linear intake/sync guide, GitHub intake guide, pack landing pages, and PM tracker-intake journey

## Fixture inputs

The walkthrough uses the checked-in `matrix.json` under each adapter's
`evals/files/intake/` directory:

- Jira `jira-default` v1.0
- Jira Align `jira-align-default` v1.0
- Linear `linear-default` v1.0
- GitHub `github-default` v1.0

Each matrix contains `direct-spec`, `multi-spec-brief`,
`cross-repo-brief`, `incoherent-collection`, `defect`, and
`claimed-defect-without-evidence`. Tracker-specific raw records vary;
normalized semantic content and expected routes match.

## Rendered routes

| Fixture | Artifact kind | Membership | Processor | Authority | Tracker write |
| --- | --- | --- | --- | --- | --- |
| `direct-spec` | spec | `work.queue` | `new-spec` | tracker-origin | none |
| `multi-spec-brief` | brief | `brief_queue.draft` | `author-brief` | tracker-origin | none |
| `cross-repo-brief` | brief | `brief_queue.draft` | `author-brief` | tracker-origin | none |
| `incoherent-collection` | intent | `draft-with-gaps` | none | tracker-origin | none |
| `defect` | defect | `backlog.open` | `bug-fix` | tracker-origin | none |
| `claimed-defect-without-evidence` | spec | `draft-with-gaps` | none | tracker-origin | none |

The real `work-intake` router returned these results for all four profiles in
`tests/roster/test_tracker_intake_adapters.py`. Replaying the corpus produced
the same route fields.

## Guide checks

- Natural-language starter requests appear before implementation detail.
- Every guide states that tracker intake is read-only and that `work-intake`
  owns repository materialization.
- Object types, hierarchy, labels, item counts, boards, sprints, cycles,
  Milestones, and queries are described as hints rather than artifact identity.
- Ambiguous collections and confidentiality mismatches retain a human decision.
- GitHub documentation assigns DNS, redirect, authentication, and transport
  behavior to approved `gh`, while documenting locally enforced host and argv
  controls.
- Linear sync remains a separate, approval-gated behavior and does not broaden
  intake's read-only boundary.

## Result

The documented direct-spec, multi-spec, cross-repository, collection, proven
defect, and unproven-defect examples match the checked-in convergence fixtures.
Source-level link, guide, catalogue, projection, and rendered-site checks are
recorded by the T7 verification run.
