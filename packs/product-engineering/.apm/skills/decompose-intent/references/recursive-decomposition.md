# Recursive decomposition + the brief projection

Decomposition produces the **next level down**, one level at a time — never a
fixed depth. The recursion is what lets one model span `app` (often one level
deep) and `business-unit` (three or more).

## One level at a time

```
intent (capability) ──decompose──▶ intent (feature) ──decompose──▶ spec / slice (leaf)
                                   intent (feature) ──decompose──▶ spec / slice
```

- **Above feature level** → produce **child intents** at the next lower `Level:`,
  each with a `Parent intent:` back-link and the parent's outcome/scope context.
  Each child re-enters at `frame-intent` → `de-risk-intent` → `decompose-intent`.
- **At feature level (the leaf)** → produce the **spec/slice**: the shippable,
  agent-buildable unit — one coherent scope, vertical (it ships and tests on its
  own), sized to what one delivery pass can carry.

## The shippability test

Cut by **what ships**, not by component or layer. "Auth service" + "auth UI" are
not two slices unless each ships and tests independently; "the slice that lets a
user reset their password, end to end" is one. A slice that can't ship on its own
isn't a slice yet — keep decomposing or regroup.

## Upward feedback

Decomposition and de-risking interleave. A child intent whose riskiest assumption
is **killed** bubbles up: it forces the parent to re-decompose (drop or replace
that branch) or, if it invalidates the parent's bet, to reframe. That upward edge
is the coupling that keeps the tree honest — a parent is only as sound as its
surviving children.

## The brief projection (`app` Scale)

A feature-level leaf intent **is** a `core` brief — the projection is identity at
`app` Scale:

| Intent field | Brief field |
| --- | --- |
| Outcome (input / lagging / guardrail) | Success metrics |
| Opportunity | Outcome (the problem + user-facing outcome prose) |
| Scope (from the parent) | Scope / Non-goals |
| (appetite, named here) | Appetite |

Write it to `docs/product/briefs/<slug>.md` and hand to `receive-brief`. No new
brief fields are needed — `receive-brief` is level-agnostic and always receives a
brief *for its own repo*. (At `business-unit` Scale the feature intent is sliced
per component into one brief per repo, each carrying a `parent-intent:` provenance
pointer — **phase 2**, out of scope for v1.)
