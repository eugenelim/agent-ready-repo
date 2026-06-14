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
that branch) or, if it invalidates the parent's bet, to reframe. Record that
re-cut on the parent's `Decomposition` (the decomposition decision, `SKILL.md`
step 2), with a pointer to the killed child's verdict — so the dropped branch
leaves a trace and isn't re-proposed later. That upward edge is the coupling that
keeps the tree honest — a parent is only as sound as its surviving children.

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
brief *for its own repo*.

## The per-component slice projection (`business-unit` Scale)

At `business-unit` Scale a feature intent fans out across many component repos,
and a polyrepo has no shared tree to spec it in. So instead of one brief, the
feature leaf is **sliced per component** into **one `core` brief per affected
repo** — cut by component here because each component repo is its own
spec-context boundary, not because component is a valid *shippability* cut (the
feature is still the shippable unit; the slices are how it crosses repo
boundaries). Read the affected components and their `providesApi`/`consumesApi`
edges and contract references from the meta-repo's catalog (the
`align-value-stream` skill owns that catalog), then stamp each slice's brief with:

- **`parent-intent:`** — an optional upward pointer to the capability/feature
  intent the slice was projected from (additive on `core`'s brief template,
  distinct from `Epic:`; `receive-brief` carries it but never interprets it).
- **A `contract@version` reference + a read-only courier snapshot** — never the
  contract copied in as authority (that forks it). See `align-value-stream`'s
  `shared-contract-handoff` reference.
- **A provider/consumer role** — which side of each `providesApi`/`consumesApi`
  edge this component is on, plus the compatibility direction.

Then seed **one rollup row per slice** in the meta-repo's cross-component rollup
so `align-value-stream` can answer "delivered across all components?" Each brief
crosses into its component repo, where `receive-brief` → `new-spec` → `work-loop`
take it the rest of the way — exactly the app-scale handoff, once per repo.
