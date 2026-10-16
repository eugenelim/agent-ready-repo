---
title: "Design the architecture"
summary: "Agree an architecture on half a page, then draw it and get it reviewed."
pack: architect
kind: how-to
uses: [architect]
aliases:
  - guides/architect/how-to/diagram-a-system
  - guides/architect/how-to/review-an-architecture-artifact
---

# Design the architecture

Name the technical choice you face, and your agent checks whether an existing design already answers it.

## Frame the choice

To check whether an earlier design already answers your question, ask:

```text
Use architect-design to decide whether our existing design for account notifications answers this new delivery-channel question before creating a new architecture artifact.
```

If it does, the agent reuses it and stops. Otherwise it asks three to five questions about what you are building, who it affects, why now, and what success looks like.

## Compare options

To get the shape agreed while changing it still costs a sentence, ask:

```text
Draft the architecture concept for account notifications.
```

The agent writes a concept of half a page: the problem, your constraints, one or two candidate shapes, the cloud provider, the top quality attributes, and the key trade-off. It waits for you to agree before going further.

## Write the design

If the concept settles the decision, stop there. If trade-offs are still open, ask:

```text
Write the full design document for the agreed concept.
```

The agent drafts the document for the scope you chose, then flags any decision worth recording as an ADR (an architecture decision record).

## Draw it

To see the design as a picture, ask:

```text
Draw the notification service as a C4 container diagram.
```

The `architect-diagram` skill picks the notation from your words, checks the Mermaid diagram against its rubric, and offers to save it. Add "as a draw.io file" to also get an editable `.drawio` file.

## Get it reviewed

To find what is wrong with a diagram or design document, paste it or give its path and ask:

```text
Review this architecture design for our payments-routing service.
```

The `architect-review` skill answers with a verdict (SHIP IT, SHIP WITH CHANGES, MAJOR REWRITE, or WRONG ARTIFACT) and findings ordered by severity, each with a suggested fix.

Next, [design the API contract](../../contracts/how-to/generate-an-api-contract.md) the architecture exposes.
