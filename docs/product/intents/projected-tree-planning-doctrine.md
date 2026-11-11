# Projected-tree planning doctrine

- **Slug:** `projected-tree-planning-doctrine`
- **Status:** Accepted
- **De-risked:** 2026-11-05
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

A plan for a change to a corpus that ships compiled is written against the tree
the guards actually read. Today a planner can enumerate authored sources, pass
every check they thought of, and still author criteria that cannot be satisfied
until a recompile happens — which they find out during execution, as an
amendment.

## The opportunity

Some guards read authored sources and some read the compiled projection, and
nothing tells a planner which is which. Two owner-authorized amendments in one
delivery came from that single blind spot. The anchor-test sweep checked digests
and counts over authored sources, while two shipped guards scan the projection:
one requires a doctrine group's provenance block to appear in the compiled body,
so the first task adding such a group cannot pass without a recompile; the other
forbids delivery-mechanic literals anywhere in the projected tree, so a
criterion requiring one was unsatisfiable and only failed once the recompile
made it visible.

A third consequence follows. Because the compiled source digest binds recorded
evaluation runs, the recompile and the re-measurement have to travel inside the
same task as the last authored edit — a later task can never share its wave, and
gates run at wave boundaries.

## What would have to be true

Before tasks are written over a compiled corpus, the planner can tell which
guards read the projection and which read the source, and places the recompile
in the task that makes the last authored edit.

Getting there needs a decision this intent does not make: whether the guard
split is knowable mechanically — derived from what each check opens — or whether
it is doctrine a maintainer states and keeps current. The mechanical route is
worth more and costs more.

## Boundary

Placement is open. The rule spans two owners and belongs to whichever is
decided, not to both:

- `packs/AGENTS.md` owns authoring inside a pack that ships compiled, and was
  the destination the observation suggested.
- `work-loop` owns wave and gate mechanics, which is what the
  recompile-inside-the-last-task half is actually about.

Splitting the rule across both would reproduce the duplication problem the
authoring rubric warns about, so this needs one home.

## Riskiest assumption

**Riskiest assumption:** a stated rule (name the guards that read the projection, and put the recompile in the task that makes the last authored edit) is enough for a planner, without a mechanical derivation of which guards read what. Tested agent-only by replaying the two recorded amendments against the rule: it must have placed the recompile so that neither amendment was needed.

## Non-goals

- Deciding whether the guard split is derived mechanically. That belongs to the closure probe in `grounding-probe-extensions`.
- Splitting the rule across `packs/AGENTS.md` and `work-loop`. It has one home.
- Any blocking check on a plan.

## De-risk result

2026-11-05, replay. The captured observation names two guards that read the compiled projection. Both exist: `packs/agent-skill-engineering/tests/pack/test_corpus_admission.py` reads the compiled concepts under `.apm/skills/ase-okf-reference/references/okf/concepts`, and `tests/pack/test_pack_boundary.py` scans `(PACK_ROOT/".apm").rglob("*")`. Searching that pack's tests for the compiled path constants finds exactly these two, so the rule's first step (name the guards that read the projection) is a one-search action for this pack and would have named both guards before the first task.

**Verdict:** supported. The guard split is statable without a mechanical derivation for the recorded case, and a path-constant search is a cheap check the rule can cite.

## Readiness

**Route:** direct-light, one sentence of doctrine in one home.

**Home:** `work-loop`'s plan-authoring reference (`references/delivery-contract-lifecycle.md`), because the planner reads it and the wave and gate mechanics it must respect live there. `packs/AGENTS.md` stays out, so the rule has one owner.

**Rule to write:** before tasks are written over a corpus that ships compiled, list which guards read the projection and which read authored sources, and put the recompile and re-measurement in the task that makes the last authored edit.

**Current truth.** No file in `packs/AGENTS.md` or the work-loop references says this today. A guard that reads the compiled body exists in `packs/agent-skill-engineering/tests/pack/test_corpus_admission.py`. Whether the guard split can be derived mechanically is not needed for the doctrine, and the closure probe in `grounding-probe-extensions` is where that answer would land.

**Agent-only proof:** a pin in the pack suite on the rule's key phrase, following the existing `RULES` pattern.

## Provenance

Mechanism and measurement are recorded as captured observation
`kco-202609-3f7fc5a7b47a27460eb6d6f831de80119400924c8dd9b5d5fa09b2c88f863bc8`
in `docs/knowledge/observations/gotcha/2026-09.jsonl`, distilled to topic
`plan-a-corpus-change-against-the-projected-tree-not-the-authored-one`.
