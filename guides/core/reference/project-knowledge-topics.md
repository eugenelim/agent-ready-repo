---
title: Project knowledge topics
summary: Topic fields, the scope format, lifecycle and retirement rules, and how a bounded enquiry selects what it returns.
pack: core
kind: reference
---

# Project knowledge topics

Authoritative field and matching rules for a **project-knowledge topic** — the distilled, committed form of a captured lesson. For the workflow that produces and retires topics, see [How to distill captured project knowledge](../how-to/distill-captured-project-knowledge.md).

## Scope

`scopes` is the field that decides whether a topic is ever found. It is a **list of repository-relative paths**.

```
scopes: ["packs", "tools"]        correct
scopes: ["."]                     correct — applies repository-wide
scopes: ["packs/**"]              WRONG — a glob is not a path
scopes: ["packs,tools"]           WRONG — one comma-joined string, not two entries
```

Rules:

- One path per list entry. Several scopes means several entries, never one delimited string.
- No globs. A path names a region already; `**` and `*` segments are not interpreted.
- `.` is the only wildcard, and means the whole repository.
- Paths are repository-relative and normalized. No leading `/`, no `..`, no drive letters.

### How a scope is matched

A topic matches a query when one of its scopes is **the same as, or an ancestor of**, the queried path.

| Topic scope | Query | Matches |
|---|---|---|
| `packs` | `packs` | yes |
| `packs` | `packs/core` | yes — the scope is an ancestor |
| `.` | anything | yes |
| `packs/core/scripts` | `packs` | **no** — the scope is a descendant, not an ancestor |
| `tools` | `packs` | no |

The descendant direction does not match. A topic scoped to a deep path is invisible to a query for its parent, so scope a topic at the level a reader would actually ask about — usually the directory that owns the behaviour, not the single file where you happened to hit it.

:::caution
A malformed scope fails silently. It does not error at write time; the topic is simply never returned. In one repository, 55 of 76 topics carried glob scopes and 30 stored several scopes as one comma-joined string. A scoped enquiry reached 21 of those 76 topics. Repairing the scopes to plain paths took it to all 76 with no code change — the topics had been there the whole time, unreachable.
:::

## Lifecycle

| `lifecycle` | `freshness.state` | Meaning |
|---|---|---|
| `active` | `fresh` | Returned by enquiry. |
| `needs_review` | `review_required` | Held back pending review. |
| `retired` | `retired` | Kept for readers arriving from a stale reference; never returned by enquiry. |

The three pair strictly: an `active` topic must be `fresh`, a `retired` topic must be `retired`. A mismatch is rejected.

### Retirement

A retired topic carries a `retirement` block:

```
reason:             enforced | canonicalized | obsolete | merged | invalidated
successors:         list of repository-relative paths
coverage_verified:  true | false
```

- `enforced` — a check now rejects the mistake.
- `canonicalized` — a convention or architecture document now states the rule.
- `merged` — another topic absorbed it.
- `obsolete` — the code or constraint is gone.
- `invalidated` — the lesson was wrong.

`enforced`, `canonicalized`, and `merged` require at least one successor and `coverage_verified: true`. The other two may retire without successors, because nothing survives to point at.

## Provenance

| Field | Meaning |
|---|---|
| `owning_source` | The artifact the topic is about. |
| `supporting_sources` | Other artifacts the lesson draws on. |
| `occurrences[].producer` | The workflow that captured it. |
| `occurrences[].reviewed_disposition` | `promoted` for a distilled topic; `active_import` or `needs_review_import` for one written by a migration. |

A `*_import` disposition means the topic entered without passing distillation's triage. Treat those as unreviewed until someone has read them.

The freshness anchor is deliberately separate from the owning source. The owning source answers *what is this topic about*; the anchor answers *what content would have to change for this topic to go stale*. They are often different files, and collapsing them ties staleness to the wrong one.

## Enquiry limits

Enquiry is bounded and returns a receipt alongside the evidence.

| Limit | Value |
|---|---|
| Topic bodies returned per query | 12 |
| Whole-invocation time budget | 30s |

Selection excludes any topic that is not `active`, not `fresh`, past its `review_after`, out of scope, or outside the requested competency facet. What remains is ordered by competency-facet match, then by topic key, and truncated to the body limit.

:::note
There is no relevance ranking within that order. A broad query that matches more topics than the limit returns an alphabetical slice of them, silently. Scope a query to the area you are actually working in rather than asking repository-wide.
:::

## Enquiry request fields

| Field | Required | Notes |
|---|---|---|
| `task_summary` | yes | What you are doing. Up to 1000 characters. |
| `scope` | yes | A repository-relative path, or `.`. |
| `question` | yes for a human caller | Free text. |
| `question_id` | — | A competency facet; filters to topics carrying it. |
| `caller` | — | `human` (default) or `skill`. |
| `risk` | — | `routine` or `consequential` (default). |

Retrieved topics are evidence, not instructions. They cannot grant permission, change scope or tooling, or override a canonical artifact.
