# Discovery writer inventory

Derived at T3 with one bounded search:
`grep -rlE "Discovery:" packs/*/.apm packs/*/seeds guides docs/guides .claude .agents .cursor .github .gemini`,
tests and `tests/` or `test/` directories dropped (47 files). The same Markdown derivation is
pinned by `tests/roster/test_graph_pointer_authoring.py` (`derive_discovery_candidates`,
`DISCOVERY_MANIFEST`). Roles are recorded separately.

## Instruction (edited: typed intent form plus repository path for research or notes)

- `packs/core/.apm/skills/new-spec/SKILL.md` (Discovery bullet in the header step)
- `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md` ("Discovery up-edge")
- `guides/core/how-to/close-and-disposition-work.md` (`delivery-target-missing`,
  `delivery-reference-malformed`, `delivery-reference-unsafe`, `artifact-not-in-graph` entries list
  `outcome`, `opportunity`, `capability`, `intent`; legacy paths described as still readable)

## Template (edited)

- `packs/core/.apm/skills/new-spec/assets/spec.md` (line 8 comment)

## Example

None. No example spec in a shipped source writes a populated `Discovery:` value.

## Generated-copy (not edited; refreshed by self-host in T4)

- `.claude/skills/new-spec/{SKILL.md,assets/spec.md,references/spec-and-plan-contract.md}`
- `.agents/skills/new-spec/{SKILL.md,assets/spec.md,references/spec-and-plan-contract.md}`
- `.claude|.agents/skills/navigate-intents/SKILL.md` (copies of an excluded reader)

## Excluded (reads or describes the field; instructs no value form)

- `guides/core/how-to/start-the-work.md`: only the sentence listing checked fields gains `Discovery:`.
- `packs/product-engineering/.apm/skills/discovery-loop/SKILL.md`: names the up-edge header as a
  lint prerequisite (lines 332, 405) and a loop-shape remark (394); never says what to write. Unchanged.
- `packs/core/.apm/skills/navigate-intents/SKILL.md`, `guides/core/how-to/navigate-intents.md`:
  describe the pointer fields the reader follows.
- `packs/core/DESIGN.md`: design record of the reader.
- Scripts that parse or resolve the field (resolver copies, `intent_graph.py`, `closure_index.py`,
  `navigate_intents.py`, `lint-traceability.py`, `lint-graph-pointers.py`) and their generated
  copies under `.claude` and `.agents`: readers, not writers.
- `packs/core/.apm/skills/{work-loop,close-work}/evals/evals.json` and copies: eval prompts that
  mention `Discovery:` fields as refusal scenarios; no instructed value form.

Kill condition not met: no candidate needed another pack or another pointer field.
