# Asset: the plan-tree template

This is the **instantiable scaffold** for the recursive intent tree
(`_state/plan-tree.json`). `discovery-lead` **copies it to start an initiative**
and fills it in as the loop runs. It is what makes "HTN-over-blackboard, no
engine" a *concrete artifact the controller fills and the traceability lint
walks* — **there is no planner engine; the template is the mechanism.**

A **node** is an `intent` slot + `parent_id` (so the tree nests) +
a **per-node status lifecycle** + the **two extension** shapes (a candidate set +
selection, and a validation status + hook). One plan-tree per initiative; relate
initiatives by stable id, never by sharing a tree.

## The four per-node namespaces

Each node carries (and the conformance lint walks):

- **`lifecycle`** — `draft → diverging → converging → ratified | stale`, plus
  `parked` / `abandoned`.
- **`validation_status`** — `hypothesis → validating → validated | refuted`. This
  makes *converged ≠ validated* a **structural property of the tree**: a node may
  be `ratified` (lifecycle) yet still `hypothesis` (validation).
- **`candidates` + `selection`** (at a divergence point) — N sibling candidate
  shapes under a `diverging` parent, and the one promoted to `converging`. The
  **not-chosen are retained** as `rejected` / `parked` **with rationale** — never
  deleted, so they stay revivable (durable persistence + `decision-archaeology`'s
  revival check).
- **`validation_hook`** — the kill-condition + the real-world activity that would
  confirm or enrich the node's load-bearing assumption.

## The instantiable template (copy this)

```json
{
  "initiative": "<initiative-slug>",
  "schema_version": "0.1",
  "root_id": "intent:vision",
  "sub_idea_index": {
    "open": [],
    "parked": [],
    "done": []
  },
  "nodes": [
    {
      "id": "intent:vision",
      "type": "intent",
      "altitude": "product-vision",
      "parent_id": null,
      "lifecycle": "draft",
      "validation_status": "hypothesis",
      "round": 0,
      "round_cap": 12,
      "cost_spent": 0.0,
      "candidates": [],
      "selection": null,
      "validation_hook": null
    }
  ]
}
```

A divergence node, once `explore-options` has generated shapes, looks like:

```json
{
  "id": "intent:cap.household-coordination",
  "type": "intent",
  "altitude": "capability",
  "parent_id": "intent:vision",
  "lifecycle": "diverging",
  "validation_status": "hypothesis",
  "round": 1,
  "round_cap": 12,
  "cost_spent": 0.8,
  "candidates": [
    {"id": "cand.kitchen-draft-approve", "altitude": "narrow-slice", "mechanic": "draft-and-approve", "riskiest_assumption": "users want approval-gated drafting", "status": "rejected", "rationale": "myopic — misses whole-household altitude"},
    {"id": "cand.whole-household-coord", "altitude": "whole-domain", "mechanic": "coordination-layer", "riskiest_assumption": "one assistant can span calendar+travel+budget", "status": "selected"}
  ],
  "selection": "cand.whole-household-coord",
  "validation_hook": {
    "assumption": "a household will delegate cross-domain coordination to one assistant",
    "kill_condition": "<3/8 pilot households delegate beyond one domain",
    "activity": "diary study + Wizard-of-Oz coordination pilot"
  }
}
```

## The sub-idea index

`sub_idea_index` lists which sub-walks are **open / parked / done**, so a
sub-idea like "recipe integration" is a **first-class, resumable node**, not a
second project. A `parked` node persists in this index (Tier 1) and is promoted
to the committed backlog as a first-class entry on teardown (Tier 2). A resumed
node knows where it is from its `lifecycle` + `validation_status`.

```json
"sub_idea_index": {
  "open": ["intent:cap.household-coordination"],
  "parked": ["intent:sub.recipe-integration", "intent:sub.budget-module"],
  "done": []
}
```

## How the controller walks it (no engine)

1. **Descend depth-first.** Pick the next node by `lifecycle`; decompose it into
   children (`parent_id`), or — at a divergence point — generate `candidates` via
   `explore-options` and record a `selection`.
2. **Account spend per branch.** Increment the node's `round` / `cost_spent`; the
   `meta` block bounds the whole initiative. A node exceeding the **concentration
   bound** (~40% of budget) or the **depth/breadth** structural bounds pauses the
   loop at `paused-at-bound` — never a silent stop.
3. **Validate, don't just converge.** When a node ratifies, set its
   `validation_status` and attach a `validation_hook` (via `plan-validation`); the
   provisional spine at G2 labels every node **grounded** / **surfaced** /
   **to-validate**.
4. **Surface descend-vs-park.** Choosing the next node, accounting spend, and
   deciding descend-vs-surface is itself scheduling the controller does
   in-context — **a defensible bet on a shallow tree**, gated by the
   depth/breadth bounds. Scheduling many concurrent / long-parked threads stays
   the **harness's** job.

The traceability lint walks the produced `_state/traceability.json` edge set; the
plan-tree's nesting (`parent_id`) and the cascade transition (walk out-edges →
mark `stale`) operate over the same node ids.
