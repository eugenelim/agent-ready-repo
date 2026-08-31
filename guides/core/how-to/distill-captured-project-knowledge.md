---
title: How to distill captured project knowledge
summary: Drain pending observations, decide each one's disposition, and retire lessons that a doc or check now enforces.
pack: core
kind: how-to
---

# How to distill captured project knowledge

**Use this when:** Workflows have been capturing lessons for a while and you want to turn the pending pile into knowledge people can actually retrieve — or act on.
**Prerequisites:** `core` installed, a terminal or agent session in the repo root, and a clean working tree.
**Result:** Every pending observation carries one terminal disposition, wrong lessons are corrected, and lessons that a doc or check now enforces are retired.

Ask for it in plain language:

```
Run a project-knowledge distillation and tell me what to do with the results
```

Capture is optional at workflow gates and uses the producer profile when a workflow provides one. Distillation is the step that decides what each captured lesson is *for*. Until an observation is dispositioned it stays pending, and a pending observation is invisible to every enquiry — so an undrained pile is knowledge you are paying to collect and cannot read.

For the exact shape of a topic and how scopes are matched, see [Project knowledge topics](../reference/project-knowledge-topics.md).

## Prerequisites

- The `core` pack installed in the target repo.
- A clean working tree. Distillation writes topic files and rebuilds the topic map; you want those changes reviewable on their own.

## Step 1 — Drain the pending observations

A maintainer draining everything asks for the repo-wide scope:

```bash
echo '{"selection_mode":"direct-maintainer-pending","scope":"."}' \
  | project-knowledge --distill --pending
```

`scope` is required. `.` means the whole repository; narrow it to a path to drain one area. The other selection mode, `workflow-receipts`, belongs to a workflow draining only the captures from its own gate — it refuses invented capture IDs, and a maintainer sweep must not use it.

The receipt reports `counts.pending`. Read each observation's `lesson` before deciding anything: the disposition is a semantic judgement, and nothing downstream re-checks it.

## Step 2 — Give each observation one disposition

Every observation gets exactly one terminal disposition. Choose by asking where the lesson's home is:

| Disposition | Choose it when |
|---|---|
| `promoted` | The lesson is durable, reusable, and no existing artifact owns it. It becomes a topic. |
| `routed` | The lesson's home is a canonical artifact — an architecture doc, a decision record, an initiative. Send it there instead of creating a topic that would duplicate a fact with an owner. |
| `rejected` | The lesson is already canonical in its owning artifact. Recording it again just creates a copy that will drift. |
| `duplicate` | An existing topic already carries this lesson. |
| `superseded` | A later observation replaced this one. |

Two rules that are easy to get wrong:

Correct wrong knowledge here, not somewhere else. If an observation contradicts a topic, or a topic turns out to be false, fix it during distillation. Filing a task to fix knowledge later routes around the mechanism that exists to keep knowledge true.

A lesson with a canonical home is routed, not promoted. Promoting it puts the same fact in two places with nothing reconciling them, and the copy in the knowledge store is the one nobody updates.

## Step 3 — Correct a topic that is wrong

Do not hand-edit a topic file. Direct edits bypass the writer lock and the field validation, and leave the topic map stale.

Correct a topic by capturing the corrected lesson and promoting it over the existing one, with `expected_topic_digest` set to that topic's current digest. The digest is a precondition: if anything changed the topic since you read it, the write is refused rather than silently overwriting. Set it to `null` only when creating a topic that does not exist yet.

## Step 4 — Retire what a doc or a check now enforces

This is the step that makes the store worth keeping, and it is the one most often skipped.

For each topic you touch, ask: **does an artifact now enforce this lesson?** If a linter rejects the mistake, or a convention document states the rule, the topic has done its job and should be retired so the enforcing artifact is the single source.

Retiring a topic sets `lifecycle` to `retired`, sets `freshness.state` to `retired`, and adds a `retirement` block naming the reason and the successors:

```
reason:             enforced | canonicalized | obsolete | merged | invalidated
successors:         the artifacts that now carry the rule
coverage_verified:  true
```

`enforced`, `canonicalized`, and `merged` require at least one successor and `coverage_verified: true` — you are asserting the lesson survives elsewhere, so name where. Rewrite the retired topic's body to state the disposition, so a reader arriving from a stale reference finds the resolution instead of a warning that no longer applies.

A store where nothing is ever retired is a store that only grows. If no topic has been retired, that is a signal the promotion step is not happening — not that every lesson is still live.

## Step 5 — Review the diff and commit

Distillation writes topic files, rebuilds the topic map, and appends disposition events to the observation journals. Journals are append-only: draining adds a disposition event and removes nothing, so the journals grow with every pass.

Commit the knowledge changes on their own. They are easier to review and to revert than a mixed change.

## If the corpus was migrated rather than captured

A corpus imported from an earlier format arrives already active, marked `active_import` or `needs_review_import`. Those topics never passed the triage in Step 2 — the import wrote them directly.

Treat an imported corpus as unreviewed until you have read it. In one repository, 64 of 76 topics had arrived by import and only 12 had ever been distilled; the first wrong topic found was an imported one. That is not a failure of capture or distillation, which never saw it. Work through imported topics the same way: read the lesson, check it against the current tree, then correct, retire, or leave it.

## Next

- [Project knowledge topics](../reference/project-knowledge-topics.md) — topic fields, scope format, and how enquiry selects.
- [The core pack](../explanation/core-pack.md) — where this surface sits among the pack's other skills.
