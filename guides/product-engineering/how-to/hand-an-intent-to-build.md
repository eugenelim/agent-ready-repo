---
title: Hand an intent to build
summary: Hand a shaped intent to Core intake so it can select the right repository-work route without losing its boundaries or provenance.
pack: product-engineering
kind: how-to
---

# Hand an intent to build

**Use this when:** A shaped intent is ready to become repository work.
**Prerequisites:** `product-engineering` and `core` packs installed; a shaped intent with a confirmed outcome and boundaries.
**Result:** A Core intake route that preserves the handoff context and stops at the next required approval gate.

Your shaping work has named the outcome and boundaries. Start the Core handoff with them intact:

```text
Start this shaped intent through Core intake: workspace owners need export retention controls, with the confirmed outcome and boundaries preserved.
```

Core's `work-intake` writes the canonical artifact, registers it in
`workspace.toml`, and reports the route. It dispatches a processor only after
both writes succeed.

## Choose the route

- One independently shippable feature goes to `new-spec`.
- A coherent outcome that needs several specs or repositories goes to
  `author-delivery-brief create`.
- A cited regression goes to `bug-fix`.

If the work only needs minimum repository admission before a solution artifact
is selected, Core uses `intake-intent`. That route creates or updates the
repository intent and stops after admission; it does not begin delivery work.

The handoff supplies bounded context and provenance. It does not approve an
artifact or skip a human gate, so continue only when Core shows the next route
and its required approval.

## What you have now

- A bounded Core intake request that carries the shaped intent's outcome and boundaries into repository work.
- The canonical artifact path, `workspace.toml` registration, and next processor are reported by Core; follow that processor's approval gate before implementation.
