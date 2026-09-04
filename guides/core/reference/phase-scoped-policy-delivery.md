---
title: "Phase-scoped policy families"
summary: Look up how a policy family is declared, how its enforcement tier is chosen, and how to diagnose a selection that returns the wrong families or refuses outright.
pack: core
kind: reference
---

# Phase-scoped policy families

:::note
Authoritative description of the **policy-family registry** in the `work-loop`
skill and the **selector** that reads it. The registry decides which behavioural
rules a work-loop phase teaches; the selector turns a phase into an ordered list
of them. Selection only — assembling the teaching text into an agent's brief, and
checking that it arrived, are separate capabilities.
:::

A **policy family** is one behavioural rule with a single owning file. Five ship
today: `observable-outcome`, `repository-anchoring`, `new-spec-step-5a`,
`the-razor`, and `cognitive-load`.

The registry lives at
`.claude/skills/work-loop/references/policy-families.md` (or
`.agents/skills/work-loop/references/policy-families.md`, depending on your
adapter) as one fenced `json policy-registry.v1` block. The prose around it is
for you; the block is what the selector reads.

## Declaring a family

Add a record to the `families` array and give it an entry in every `selection`
key that should teach it. A record carries three fields:

- **`id`** — a stable identifier. It appears in the delivery record and in
  arrival verdicts, so renaming one is a contract change, not a tidy-up.
- **`tier`** — `precise` or `advisory`. See the next section.
- **`module`** — a *logical locator*, never a path.

The locator matters more than it looks. Write `skill:new-spec/assets/spec.md`,
not `packs/core/.apm/skills/new-spec/assets/spec.md`: the registry ships to your
repository, where the catalogue path does not exist and the same rule lives under
`.claude/skills/` or `.agents/skills/`. Two namespaces are recognised —
`skill:<name>/<relative-path>` for a rule owned by a skill, and `seed:<path>` for
one owned by a file seeded into your repository root.

Point a locator at the file that **owns** the rule. Where a generated projection
and its source both exist, the source is the owner — `the-razor` is
`seed:AGENTS.md` rather than a projected copy.

A family you add but select nowhere is inert. A `selection` key you leave empty
is a deliberate answer, not a gap: the human-gate and terminal states select
nothing because no agent is authoring while the loop waits in them.

## Classifying a family

Every family is `precise` or `advisory`. There is no middle tier.

**`precise`** means a parse-level predicate can decide the rule against the
produced artifact. Only a precise family can ever block.

**`advisory`** means the rule is taught and reported but never blocks. Choose it
when deciding the rule needs a judgement rather than a parse — including when the
decidable evidence exists but lives outside the artifact, such as a rule about
whether a search was run.

The safe default is `advisory`. A family shipped `precise` on an undecidable
predicate produces false blocks, which is worse than teaching a rule you cannot
yet enforce. Two of the five ship `precise` today; three are advisory.

Splitting helps. A rule that needs a reasoned verdict often divides into a
decidable part and a smaller semantic residue — ship the decidable part as its
own `precise` family and leave the residue advisory, rather than forcing the
whole rule into one tier.

## Troubleshooting a selection

Run the selector directly. It takes the registry, a resolution root, and a
selection key:

```bash
python3 .claude/skills/work-loop/scripts/select-policy-families.py \
  --registry .claude/skills/work-loop/references/policy-families.md \
  --root . \
  CODE-IMPLEMENTATION
```

Every refusal prints to stderr with a `select-policy-families:` prefix and exits
non-zero. The record goes to stdout and nothing else does, so piping into a JSON
parser is safe.

| What you see | What it means |
| --- | --- |
| `unknown selection key 'X'` | `X` is not an `engine-state.json.state` value or the reserved token. Selection never infers a phase from prose — check what the engine actually recorded. |
| `module 'Y' resolves to no file under Z` | The locator is right but the file is not installed under `--root`, or `--root` points at the wrong tree. |
| `info string ... disagrees with schema_version` | The fence's version token and the block's `schema_version` diverged. Both must move together. |
| `unsupported schema_version` | The registry was written for a newer selector than the one installed. |
| `duplicate family id` / `selection 'X' repeats a family id` | The same family appears twice. Selection is an ordered set. |
| `family 'Y' has tier ...` | Only `precise` and `advisory` exist. |

**`--root` is not always where the registry lives.** The registry travels with
the skill, while `seed:` rules live at your repository root. Pointing `--root` at
a projection output directory makes every `seed:` family unresolvable — pass the
repository root instead.

**The light path uses `DIRECT-LIGHT`.** A direct-light change creates no engine
state, so there is no FSM value to key on. It is a declared constant, and it is
the only reserved token.

**An empty result for a gate or terminal state is correct.** If a state that
*should* teach something returns nothing, the `selection` map has been thinned —
compare it against the registry suite's literal expectation.
