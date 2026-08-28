---
title: Choose a tracker integration for work intake
summary: Select the appropriate tracker intake route while keeping tracker object types separate from repository artifact routing.
pack: _shared
kind: how-to
---

# Choose a tracker integration for work intake

**Use this when:** tracked work should become canonical repository work.
**Result:** the same content-based route whether the source is Jira, Jira
Align, Linear, or GitHub.

Start with a request such as:

```text
Intake this tracker selection as repository work. Start read-only.
```

The tracker adapter reads and minimizes source data. It does not decide that an
Epic, Feature, Project, or Milestone is a brief. It sends validated normalized
content to `work-intake`, which selects the artifact, lifecycle membership,
processor, and authority mode.

## Choose by source

| Source | Pack | Example request |
| --- | --- | --- |
| Jira | `atlassian` | `Intake Jira issue PROJ-123 as repository work.` |
| Jira Align | `atlassian` | `Intake Jira Align Feature 4521 as repository work.` |
| Linear | `linear` | `Intake Linear issue LIN-123 as repository work.` |
| GitHub | `github` | `Intake GitHub issue 123 as repository work.` |
| No tracker | `core` | `Start work from this description: …` |

Install `core` in the repository and the tracker pack at the scope where its
credentials belong. Jira, Jira Align, and Linear use their sibling acquisition
skills. GitHub uses approved `gh` reads against a trusted configured host.

## Check the proposed route

The same five fixture shapes produce the same route across all four profiles:

| Content found | Route |
| --- | --- |
| One independently shippable, verifiable behavior | spec → `new-spec` |
| One coherent outcome that needs several specs | Draft brief → `author-delivery-brief create` |
| One outcome spanning repositories | linked local briefs with parent and coordination provenance |
| Unrelated collection or view | separate units, a view-only result, or one clarifying question |
| Regression with durable expected-behavior evidence | defect context → `bug-fix` |

A tracker label, item count, title, or hierarchy position cannot override this
content. A claimed defect without durable evidence remains unresolved or enters
the spec route.

## Read and write boundary

Intake is read-only against every tracker. It never creates, edits, comments,
labels, transitions, or closes tracker work. It also never writes a repository
artifact directly.

After strict validation, `work-intake` may materialize and register the selected
repository artifact. It asks first when the selection cannot be distinguished as
one outcome, separate units, or a view, or when source confidentiality exceeds
the destination.

If `work-intake` is missing, the adapter returns
`missing dependency: work-intake` and stops. There is no local fallback.

After intake has created a tracker-origin artifact, a later refresh is a
separate workflow. It compares the registered source revision, requires local
field decisions, and may offer only the coordination write-back actions
declared by that exact profile. Every remote mutation requires its own fresh
confirmation; intake itself remains read-only.

## Limits

Every profile declares page, item, byte, timeout, retry, and backoff limits.
Exhaustion is explicit: the result is marked incomplete or refused as view-only.
Tracker text is untrusted data and cannot change the destination, command,
tools, routing, or authority.

## Next request

After reviewing the route, answer any named gap or confidentiality question.
Then continue with the selected processor, such as `new-spec`, `author-delivery-brief create`,
or `bug-fix`. For an existing artifact whose tracker source changed, follow
[Use work intake](use-work-intake.md).

## See also

- [Tracker vocabulary](../reference/tracker-vocabulary.md)
- [Use work intake](use-work-intake.md)
- [Start or remember work](../../core/how-to/start-or-remember-work.md)
- [GitHub intake](../../github/how-to/intake-a-github-milestone-as-a-brief.md)
- [Linear intake and sync](../../linear/how-to/linear-brief-intake-and-sync.md)
