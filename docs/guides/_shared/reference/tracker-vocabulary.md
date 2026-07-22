# Tracker vocabulary

Maps the same conceptual levels (brief, spec) to the corresponding object in each
supported tracker. Use this when setting up a tracker integration or when vocabulary
between tools is causing confusion.

## Object-level mapping

Each tracker slices the intent hierarchy differently. The two levels that matter for
the brief-intake pipeline are:

- **Brief level** — a body of multi-feature work that arrives as a handoff; maps to
  the object you pull with the tracker's intake skill.
- **Spec level** — one independently shippable feature; maps to the leaf object.

| Level | No tracker | GitHub | Linear | Jira | Jira Align |
|---|---|---|---|---|---|
| **Brief** (multi-feature body) | `docs/product/briefs/<slug>.md` | Milestone | Project *or* Issue (with sub-issues) | Epic | Feature |
| **Spec / leaf** | `docs/specs/<slug>/` | Issue | Sub-issue | Issue / Story | Story / sub-task |

### Notes

- **GitHub** has no Epic or Feature object type. A Milestone groups issues at the brief
  level; individual Issues are the leaf.
- **Linear** has no Epic or Feature object type. An Issue with sub-issues acts as the
  brief-level container; the sub-issues are the leaf. A Project groups issues at one
  level above.
- **Jira** and **Jira Align** use the same word "Feature" for different levels —
  a Jira Align Feature is a program-level unit; in Jira Software "Feature" may be an
  Epic-level label. The mapping resolves by tracker, not by word.
- **Jira Align** expands the hierarchy near 1:1 with the canonical intent tree; Linear
  collapses it (three native levels vs. six in Jira Align).

## Brief-intake skill routing

| Tracker | Brief-level object | Skill | Pack | Auth |
|---|---|---|---|---|
| No tracker | Unstructured input | `author-brief` | `core` | None |
| GitHub | Milestone | `github-brief-intake` | `github` | `gh auth login` (private repos); anonymous for public |
| Linear | Issue (with sub-issues) or Project | `linear-brief-intake` | `linear` | Personal API key via `credential-setup` |
| Jira | Epic | `jira-brief-intake` | `atlassian` | API token via `credential-setup` |
| Jira Align | Feature | `jira-align-brief-intake` | `atlassian` | API token via `credential-setup` |

After intake, all paths hand off to `receive-brief` (core) to elicit gaps, decompose
into specs, and chain `new-spec` → `work-loop`.

## Why the mapping is one-way

The intent tree is deeper than any tracker. The tracker is a lossy, one-way
**projection** of it — the intent tree is the source of truth, and the tracker is a
render. Never model the work inside the tracker: you model in intents
(`docs/specs/`, `docs/product/briefs/`) and render to whichever tracker the team uses.
Bidirectional sync across mismatched hierarchies silently corrupts the product model.

The `linear-brief-sync` skill is the sole exception: it catches up a brief from a
**changed** Linear Issue after a review round, diffing only the fields the intake
originally imported and presenting the delta for approval before writing. It is still
PE-triggered, not automatic.

## See also

- [Choose a tracker integration](../how-to/choose-a-tracker-integration.md) — which
  intake skill to use for your tracker.
- [Product brief fields](../../core/reference/product-brief-fields.md) — the brief
  field list, including the `Epic:` provenance pointer populated by tracker intake.
- [Why a brief layer](../../core/explanation/why-a-brief-layer.md) — why the brief
  sits above the spec and how it integrates with the tracker via the `Epic:` pointer.
