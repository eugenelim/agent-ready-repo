---
title: "Record a decision"
summary: "Write down a decision, or propose one for debate, so the next person can find out why."
pack: governance-extras
kind: how-to
uses: [governance-extras]
aliases:
  - guides/governance-extras/how-to/navigate-decisions
---

# Record a decision

Name a decision you made, and your agent records it as an ADR (architecture decision record): a short note that says what you chose and why.

## Write an ADR

Use an ADR for a decision already made, such as a database or a branching rule, where you weighed at least one alternative. For an idea still under debate, write an RFC (request for comments) instead. To write the ADR, name the skill and the decision:

```text
Use the new-adr skill to write an ADR for choosing PostgreSQL for the order service.
```

The agent drafts the record with the alternatives you weighed, shows you the file name and a preview, and writes `docs/adr/NNNN-<title>.md` only after you confirm. It starts as Proposed. If the repository keeps decisions elsewhere, the agent finds that folder and asks before using it.

## Accept it

Once the people who own the call agree, ask for the status to change:

```text
Mark ADR <number> as Accepted.
```

The agent updates the status from Proposed to Accepted.

## What an ADR records

An accepted ADR is immutable, so to reverse a decision, write a new ADR that supersedes it; a contested reversal should go through [an RFC first](new-rfc.md#the-rfc-lifecycle). The `adr/README.md` index is generated from the records, so regenerate it rather than editing a row. The records sit in the repository's [frozen and living layers](../../../docs/README.md#the-three-lifecycle-classes).

## Propose a change

Ask for an RFC when you want input before deciding:

```text
Use the new-rfc skill to propose moving the build to a monorepo.
```

The agent researches the question and writes `docs/rfc/NNNN-<title>.md`. [Propose a change with an RFC](new-rfc.md) covers its lifecycle.

## Find a past decision

Ask about the records already in your repository:

```text
Which ADRs are accepted, and what supersedes the decision on authentication?
```

The agent reads `docs/adr/` and `docs/rfc/`, then reports each record's status and what replaced it. Ask for an offline HTML explorer to share the whole set.

Next, [write the docs](../../product-documentation/how-to/write-a-guide.md) that explain the decision to users.
