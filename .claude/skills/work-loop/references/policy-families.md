# Phase-scoped policy families

Which policy families a work-loop phase teaches, as data. A **policy family** is
one behavioural rule with a single owning file — not a clause, and not a whole
document. The controller hands
[`scripts/select-policy-families.py`](../scripts/select-policy-families.py) one
selection key and gets back the ordered families that key selects, each with its
enforcement tier and a fingerprint of the text that teaches it.

This file is the registry. It carries prose for the maintainer and one fenced
block for the selector; the block is the authority and the only thing tests pin.

## What a family record carries

| Field | Meaning |
| --- | --- |
| `id` | Stable identifier. Appears in the delivery record and in the arrival validator's verdicts, so renaming one is a contract change. |
| `tier` | `precise` or `advisory`. Only a `precise` family may block; an advisory family is taught and reported, never enforced. There is no intermediate tier. |
| `module` | A **logical locator**, not a path: `skill:<name>/<relative-path>` or `seed:<relative-path>`. It names the file that *owns* the rule. |

A locator rather than a path, because this registry ships to adopters. The same
rule lives at `packs/core/.apm/skills/…` here and at `.claude/skills/…` or
`.agents/skills/…` on an install, so a raw path would resolve nowhere for a real
consumer. Resolution order is fixed by the spec, not by this file.

`module` names the rule's **authoring owner**. Where a projection and its seed
both exist, the seed is that owner — `.agents/rules/cognitive-load.md` is a
generated copy of `packs/core/seeds/.agents/rules/cognitive-load.md`, so the
locator is `seed:`-namespaced. Resolution deliberately reads whichever copy the
acting agent would see, which is a separate question from ownership.

## What a selection key means

The key is `engine-state.json.state` whenever a loop exists. Every legal FSM
state has an entry; the state set is owned by
[`scripts/loop-engine.py`](../scripts/loop-engine.py)'s transition tables, and a
state added there without an entry here is a defect the registry suite catches.

`DIRECT-LIGHT` is the one reserved constant. The light path creates no engine
state, so it has no FSM value to key on — the token is a declared constant, never
an inference from prose.

An empty list is a deliberate answer, not a gap. The human-gate and terminal
states (`SPEC-HUMAN-GATE`, `PLAN-HUMAN-GATE`, `SPEC-PLAN-APPROVED`,
`CODE-HUMAN-GATE`, `DONE`) select nothing because no agent authors an artifact
while the loop waits in them. Emptying any *other* key silently stops delivering
policy, which is why the selection map is pinned as a literal.

## The registry

```json policy-registry.v1
{
  "schema_version": 1,
  "families": [
    {
      "id": "observable-outcome",
      "tier": "precise",
      "module": "skill:new-spec/assets/spec.md"
    },
    {
      "id": "repository-anchoring",
      "tier": "precise",
      "module": "skill:new-spec/assets/plan.md"
    },
    {
      "id": "new-spec-step-5a",
      "tier": "advisory",
      "module": "skill:new-spec/SKILL.md"
    },
    {
      "id": "the-razor",
      "tier": "advisory",
      "module": "seed:AGENTS.md"
    },
    {
      "id": "cognitive-load",
      "tier": "advisory",
      "module": "seed:.agents/rules/cognitive-load.md"
    }
  ],
  "selection": {
    "SPEC-PLAN-DRAFTING": [
      "observable-outcome",
      "repository-anchoring",
      "new-spec-step-5a",
      "the-razor",
      "cognitive-load"
    ],
    "SPEC-PLAN-REVIEW": [
      "observable-outcome",
      "repository-anchoring",
      "new-spec-step-5a",
      "the-razor",
      "cognitive-load"
    ],
    "CODE-IMPLEMENTATION": [
      "the-razor",
      "cognitive-load"
    ],
    "CODE-VERIFICATION": [
      "the-razor",
      "cognitive-load"
    ],
    "CODE-REVIEW": [
      "the-razor",
      "cognitive-load"
    ],
    "DIRECT-LIGHT": [
      "the-razor",
      "cognitive-load"
    ],
    "SPEC-HUMAN-GATE": [],
    "PLAN-HUMAN-GATE": [],
    "SPEC-PLAN-APPROVED": [],
    "CODE-HUMAN-GATE": [],
    "DONE": []
  }
}
```

## The delivery record

One selection produces one record. Its fields:

| Field | Meaning |
| --- | --- |
| `selection_key` | The key that was used, echoed so a consumer can correlate a record with the phase that produced it. |
| `families` | The selected records in declared order, each extended with `module_digest`. |
| `module_digest` | SHA-256 of the resolved module file, 64 lowercase hex characters, no prefix. |
| `assembled_brief_digest` | **Always `null` here.** Selection does not assemble a brief, so nothing is digested over assembled text. The field is declared so the arrival validator reads one record shape rather than two, and the slice that performs assembly populates it. |

The record proves what was *selected*, never that a model obeyed it. Whether
every selected family arrived, and whether a precise one was honoured, belong to
the arrival validator.
