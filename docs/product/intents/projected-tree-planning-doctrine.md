# Projected-tree planning doctrine

- **Slug:** `projected-tree-planning-doctrine`
- **Status:** Fulfilled
- **Fulfilled:** 2026-11-12 eugenelim: compiled-corpus planning guidance and the `plan-compiled-corpus-guard-inputs` eval definition were added; `test_projected_tree_planning_doctrine.py` passes all 10 content-pin cases (nine `test_compiled_corpus_rule` cases and `test_plan_loads_the_rule_before_task_authoring`).
- **De-risked:** 2026-11-05
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

A plan for a change to a corpus that ships compiled is written against the tree
the guards actually read. Before this change, a planner could enumerate authored
sources, pass every check they thought of, and still author criteria that could
not be satisfied until a recompile happened — discovered during execution as an
amendment.

## The opportunity

Some guards read authored sources and some read the compiled projection. Before
this change, no planning rule required identifying that split. Two
owner-authorized amendments in one delivery came from that blind spot. The
anchor-test sweep checked digests
and counts over authored sources, while two shipped guards scan the projection:
one requires a doctrine group's provenance block to appear in the compiled body,
so the first task adding such a group cannot pass without a recompile; the other
forbids delivery-mechanic literals anywhere in the projected tree, so a
criterion requiring one was unsatisfiable and only failed once the recompile
made it visible.

A third consequence follows. Because the compiled source digest binds recorded
evaluation runs, the recompile and the re-measurement have to travel inside the
same task as the last authored edit, before its gates. Current execution defaults
to sequential attempts and runs gates after each implementation task; earlier
tasks that change guarded compiled content must refresh their own projections
and affected measurements too.

## What would have to be true

Before tasks are written over a compiled corpus, the planner names which guards
read the projection and which read authored sources using each guard’s input
paths. Recompilation and refreshed measurements precede every affected task’s
gates, including the task that makes the last authored edit.

A stated rule is sufficient for this slice. Mechanical derivation remains outside
its scope.

## Boundary

The rule has one home: the work-loop lifecycle reference’s “Planning a compiled
corpus” section. A conditional PLAN link loads it before tasks are written.
`packs/AGENTS.md` does not duplicate the rule.

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

**Route:** direct-light under the explicit implementation brief.

**Home:** `packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md`
owns the doctrine. This is a lifecycle reference, so the companion PLAN link in
`packs/core/.apm/skills/work-loop/SKILL.md` is needed to reach it before task
authoring. The rule covers per-task gates, not only wave boundaries.

**Proof:** pack-local content pins cover the guard split, final-task recompile
and re-measurement, earlier affected tasks, and the PLAN route. The work-loop
eval definition covers provenance-in-compiled-body and forbidden-projection-literal cases.
Content pins verify the declared guidance. Live agent-behavior replay of the new eval cases was not run and remains a follow-up check.

## Provenance

Mechanism and measurement are recorded as captured observation
`kco-202609-3f7fc5a7b47a27460eb6d6f831de80119400924c8dd9b5d5fa09b2c88f863bc8`
in `docs/knowledge/observations/gotcha/2026-09.jsonl`, distilled to topic
`plan-a-corpus-change-against-the-projected-tree-not-the-authored-one`.
