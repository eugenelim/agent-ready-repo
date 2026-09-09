# Accepted base: tutorial worked examples

Captured 2026-09-09 with:

```text
python3 tools/audit-guide-affordances.py --ledger <temporary-path>
```

This ledger freezes every in-scope tutorial that lacked demonstrated input
(`B`), sample output (`C`), or both. Corpus additions do not expand the slice.

Parent S4 boundary: “Every current in-scope tutorial target demonstrates its
workflow input and keeps it paired with a representative output and the result
shown; related-intent surfaces remain excluded.” The audit verified the
frontmatter `kind` recorded below for every row.

| Tutorial | Kind | Missing affordance |
| --- | --- | --- |
| `guides/architect/tutorials/architect-first-session.md` | tutorial | B, C |
| `guides/architect/tutorials/create-your-reference-architecture.md` | tutorial | B |
| `guides/atlassian/review-your-team-backlog.md` | tutorial | B, C |
| `guides/catalogue-curation/tutorials/first-assimilation.md` | tutorial | B, C |
| `guides/catalogue-curation/tutorials/your-first-skill.md` | tutorial | B |
| `guides/catalogue-curation/tutorials/your-first-subagent.md` | tutorial | B, C |
| `guides/core/tutorials/start-a-new-project.md` | tutorial | C |
| `guides/desk-research/tutorials/desk-research-first-session.md` | tutorial | B |
| `guides/desk-research/tutorials/your-first-research-project.md` | tutorial | B |
| `guides/figma/tutorials/figma-first-session.md` | tutorial | B |
| `guides/frontend-engineering/tutorials/scaffold-a-component.md` | tutorial | B |
| `guides/governance-extras/tutorials/governance-extras-first-session.md` | tutorial | B |
| `guides/product-documentation/getting-started.md` | tutorial | B |
| `guides/product-engineering/tutorials/walk-a-discovery-end-to-end.md` | tutorial | B, C |
| `guides/product-strategy/tutorials/run-your-first-swot.md` | tutorial | B, C |
| `guides/release-engineering/tutorials/your-first-release.md` | tutorial | B |

The already-complete core workspace tutorial carries both affordances and is
not a target. No tutorial under `guides/experience-design/**`
appears in the accepted base. New cross-pack or role-specific tutorials remain
with their related intents.
