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

A locator rather than a path, because the same rule sits at a different place in
every install: a skill's files land under `.claude/skills/` or `.agents/skills/`
depending on the adapter. A raw path would resolve nowhere for some consumer.

**What a locator can reach.** A `seed:` locator resolves against the repository
root, so it can name any file in the tree, not only seed material — `the-razor`
is the root `AGENTS.md`. That reach is deliberate, and it is the reason a
registry change deserves the same review as code: an entry naming a sensitive
file would put that file's digest in the delivery record. Resolution refuses
anything outside the root, including through a symlink or a hard link, so the
reach stops at the tree boundary.

`module` names the rule's **authoring owner** — the file a maintainer edits to
change the rule. Where a generated copy and the file it was generated from both
exist, the source is the owner. Resolution is a separate question: it reads
whichever copy the acting agent would actually see, preferring an installed or
repository-root copy over a build source, and it refuses any target that leaves
the resolution root.

## What a selection key means

The key is `engine-state.json.state` whenever a loop exists. Every legal FSM
state has an entry; the state set is owned by
[`scripts/loop-engine.py`](../scripts/loop-engine.py)'s transition tables. Adding
a state there without adding an entry here is a defect — the selector has no
answer for that phase and refuses.

`DIRECT-LIGHT` is the one reserved constant. The light path creates no engine
state, so it has no FSM value to key on — the token is a declared constant, never
an inference from prose.

An empty list is a deliberate answer, not a gap. The human-gate and terminal
states (`SPEC-HUMAN-GATE`, `PLAN-HUMAN-GATE`, `SPEC-PLAN-APPROVED`,
`CODE-HUMAN-GATE`, `DONE`) select nothing because no agent authors an artifact
while the loop waits in them. Emptying any *other* key silently stops delivering
policy for that phase, so pin the map's expected contents in whatever test suite
covers this registry rather than trusting a review to notice.

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
